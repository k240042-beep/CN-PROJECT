"""
realtime.py - WebSocket (Flask-SocketIO) side of the chat.

Events
  client -> server : "send_message" {message}, "typing"
  server -> client : "new_message" {username, message, timestamp},
                     "online_users" [names], "typing" {username},
                     "stop_typing" {username}

app.py only needs:   realtime.init_app(app)   and   realtime.run(app)
"""
import os
from datetime import datetime, timezone
from threading import Lock
from urllib.parse import quote

from flask import request, session
from flask_socketio import SocketIO, emit

import database
import ftp_server

socketio = SocketIO(async_mode="threading")

MAX_MESSAGE_LENGTH = 2000
_online = {}   # username -> set of socket ids (one user can have many tabs)
_sids = {}     # socket id -> username
_lock = Lock()


def _now():
    # same format SQLite's CURRENT_TIMESTAMP uses, so live and old messages match
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _broadcast_online():
    with _lock:
        users = sorted(_online)
    socketio.emit("online_users", users)


def _broadcast_message(username, text):
    socketio.emit("new_message", {
        "username": username,
        "message": text,
        "timestamp": _now(),
    })


# ---------- socket events ----------
@socketio.on("connect")
def on_connect():
    username = session.get("username")
    if not username:
        return False   # not logged in -> refuse the connection
    with _lock:
        _sids[request.sid] = username
        _online.setdefault(username, set()).add(request.sid)
    _broadcast_online()


@socketio.on("disconnect")
def on_disconnect():
    with _lock:
        username = _sids.pop(request.sid, None)
        if username:
            _online[username].discard(request.sid)
            if not _online[username]:
                del _online[username]
    if username:
        socketio.emit("stop_typing", {"username": username})
        _broadcast_online()


@socketio.on("send_message")
def on_send_message(data):
    username = _sids.get(request.sid)
    text = data.get("message", "") if isinstance(data, dict) else ""
    text = text.strip() if isinstance(text, str) else ""
    if not username or not text or len(text) > MAX_MESSAGE_LENGTH:
        return
    database.save_message(username, text)
    _broadcast_message(username, text)


@socketio.on("typing")
def on_typing():
    username = _sids.get(request.sid)
    if username:
        emit("typing", {"username": username}, broadcast=True, include_self=False)


# ---------- called by ftp_server when a file upload finishes ----------
def announce_upload(username, filename):
    link = "/files/" + quote(filename)   # chat.js turns this into img/audio/video/link
    database.save_message(username, link)
    _broadcast_message(username, link)


# ---------- hooks for app.py ----------
def init_app(app):
    app.register_blueprint(ftp_server.files_bp)
    socketio.init_app(app)
    return socketio


def run(app, host="127.0.0.1", port=5000, debug=True):
    # With the debug reloader the script runs twice; only the child process
    # (WERKZEUG_RUN_MAIN=true) should start FTP, otherwise the port is taken twice.
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        ftp_server.start_in_background(announce_upload, host=host)
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
