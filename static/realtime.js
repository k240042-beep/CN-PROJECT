// realtime.js - connects chat.js to the server over WebSocket (Socket.IO).
// Load AFTER chat.js and the socket.io client.
(function () {
    const socket = io();
    const form = document.getElementById("chat-form");
    const input = document.getElementById("message-input");

    // ---- incoming ----
    socket.on("new_message", function (m) {
        stopTyper(m.username);
        addMessage(m.username, m.message, m.timestamp);
    });
    socket.on("online_users", function (users) { updateOnlineUsers(users); });

    // ---- typing indicator (supports several people typing at once) ----
    const typers = {};   // username -> timeout id

    function refreshTyping() {
        const names = Object.keys(typers);
        if (names.length) { showTyping(names.join(", ")); } else { hideTyping(); }
    }
    function stopTyper(name) {
        if (typers[name]) { clearTimeout(typers[name]); delete typers[name]; }
        refreshTyping();
    }
    socket.on("typing", function (d) {
        clearTimeout(typers[d.username]);
        // if no new typing event for 3s, assume they stopped
        typers[d.username] = setTimeout(function () { stopTyper(d.username); }, 3000);
        refreshTyping();
    });
    socket.on("stop_typing", function (d) { stopTyper(d.username); });

    // ---- outgoing ----
    let lastTypingSent = 0;
    window.onTyping = function () {
        const now = Date.now();
        if (now - lastTypingSent > 1500) {   // at most one event per 1.5s
            lastTypingSent = now;
            socket.emit("typing");
        }
    };

    form.addEventListener("submit", function (e) {
        e.preventDefault();   // stop the old full-page POST to /send
        const text = input.value.trim();
        if (!text) { return; }
        socket.emit("send_message", { message: text });
        input.value = "";
        lastTypingSent = 0;
    });
})();
