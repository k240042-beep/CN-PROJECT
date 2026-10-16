const messagesDiv = document.getElementById("messages");
const typingDiv = document.getElementById("typing");
const onlineList = document.getElementById("online-list");
const messageInput = document.getElementById("message-input");

// File types we can show directly in the chat
const IMAGE_EXT = /\.(png|jpe?g|gif|webp)$/i;
const AUDIO_EXT = /\.(mp3|wav|ogg|m4a)$/i;
const VIDEO_EXT = /\.(mp4|webm|mov)$/i;

// Decides how to display a message: text, image, audio, video or file link
function buildContent(message) {
    const text = message.trim();
    const looksLikeLink = /^(https?:\/\/|\/)\S+$/.test(text);

    if (looksLikeLink && IMAGE_EXT.test(text)) {
        const img = document.createElement("img");
        img.src = text;
        return img;
    }
    if (looksLikeLink && AUDIO_EXT.test(text)) {
        const audio = document.createElement("audio");
        audio.controls = true;
        audio.src = text;
        return audio;
    }
    if (looksLikeLink && VIDEO_EXT.test(text)) {
        const video = document.createElement("video");
        video.controls = true;
        video.src = text;
        return video;
    }
    if (looksLikeLink) {
        const a = document.createElement("a");
        a.href = text;
        a.textContent = "Download file: " + text;
        return a;
    }
    const span = document.createElement("div");
    span.textContent = message;   // textContent keeps HTML/scripts harmless
    return span;
}

// Adds one message bubble to the screen
function addMessage(username, message, timestamp) {
    const bubble = document.createElement("div");
    bubble.className = "msg" + (username === CURRENT_USER ? " mine" : "");

    const name = document.createElement("div");
    name.className = "msg-name";
    name.textContent = username;

    const time = document.createElement("div");
    time.className = "msg-time";
    time.textContent = timestamp || "";

    bubble.appendChild(name);
    bubble.appendChild(buildContent(message));
    bubble.appendChild(time);
    messagesDiv.appendChild(bubble);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;   // scroll to newest
}

// Dev will call this with a list of usernames, e.g. ["manahil", "dev"]
function updateOnlineUsers(users) {
    onlineList.innerHTML = "";
    users.forEach(function (u) {
        const li = document.createElement("li");
        li.textContent = u;
        onlineList.appendChild(li);
    });
}

// Dev will call these for the typing status
function showTyping(username) { typingDiv.textContent = username + " is typing..."; }
function hideTyping() { typingDiv.textContent = ""; }

// Tells Dev's code when the user types (he sets window.onTyping)
messageInput.addEventListener("input", function () {
    if (typeof window.onTyping === "function") { window.onTyping(); }
});

// Show saved history when the page loads
HISTORY.forEach(function (m) { addMessage(m.username, m.message, m.timestamp); });
if (HISTORY.length === 0) { typingDiv.textContent = "No messages yet. Say hello!"; }

// For now, only you are shown as online
updateOnlineUsers([CURRENT_USER]);
