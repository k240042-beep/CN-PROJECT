"""
ftp_server.py - FTP file sharing for the chat app.

* Users log in to FTP with the SAME username/password they registered with.
* Everyone shares one folder: ./uploads
* When a file finishes uploading, the chat is told (via the callback given to
  start_in_background) and the file shows up in the chat as a link.
* The Flask blueprint `files_bp` serves those files at /files/<name> so that
  chat.js can show them as image / audio / video / download link.
"""
import os
import threading

from flask import Blueprint, abort, send_from_directory, session
from pyftpdlib.authorizers import AuthenticationFailed, DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
from werkzeug.security import check_password_hash

import database

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
FTP_PORT = 2121
PASSIVE_PORTS = range(60000, 60010)
# e = cd, l = list, r = download, w = upload. No delete/rename, so users
# cannot remove each other's files.
PERMISSIONS = "elrw"

_on_upload = None   # callback(username, filename), set by start_in_background


# ---------- HTTP side: lets the browser open uploaded files ----------
files_bp = Blueprint("files", __name__)


@files_bp.route("/files/<path:filename>")
def serve_file(filename):
    if "username" not in session:
        abort(401)
    return send_from_directory(UPLOAD_DIR, filename)


# ---------- FTP side ----------
class DBAuthorizer(DummyAuthorizer):
    """Checks FTP logins against the users table (hashed passwords)."""

    def validate_authentication(self, username, password, handler):
        user = None if username.lower() == "anonymous" else database.get_user(username)
        if not user or not check_password_hash(user["password_hash"], password):
            raise AuthenticationFailed("Wrong username or password.")
        if not self.has_user(username):
            try:
                self.add_user(username, "", UPLOAD_DIR, perm=PERMISSIONS)
            except ValueError:   # another thread added it first
                pass


class ChatFTPHandler(FTPHandler):
    def on_file_received(self, file):
        if _on_upload:
            _on_upload(self.username, os.path.basename(file))


def start_in_background(on_upload, host="127.0.0.1", port=FTP_PORT):
    """Starts the FTP server in a daemon thread and returns immediately."""
    global _on_upload
    _on_upload = on_upload
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ChatFTPHandler.authorizer = DBAuthorizer()
    ChatFTPHandler.passive_ports = PASSIVE_PORTS
    ChatFTPHandler.banner = "Chat portal FTP ready. Log in with your chat username."

    server = ThreadedFTPServer((host, port), ChatFTPHandler)
    # handle_exit=False: signal handlers can only be set in the main thread
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"handle_exit": False}, daemon=True
    )
    thread.start()
    print(f"[ftp] listening on {host}:{port}, sharing {UPLOAD_DIR}")
    return server
