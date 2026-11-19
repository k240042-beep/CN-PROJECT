from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import database
import realtime

app = Flask(__name__)
app.secret_key = "change-this-to-any-random-text"   # needed for sessions

database.init_db()   # create the tables when the server starts
realtime.init_app(app)


@app.route("/")
def home():
    # Logged-in users go to chat, others go to login
    if "username" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if username == "" or password == "":
            flash("Please fill in all fields.")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
        else:
            hashed = generate_password_hash(password)   # never store the real password
            if database.add_user(username, hashed):
                flash("Account created! Please log in.")
                return redirect(url_for("login"))
            else:
                flash("Username already taken.")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = database.get_user(username)
        if user and check_password_hash(user["password_hash"], password):
            session["username"] = username   # remember the user is logged in
            return redirect(url_for("chat"))
        flash("Wrong username or password.")
    return render_template("login.html")


@app.route("/chat")
def chat():
    if "username" not in session:   # block access without login
        return redirect(url_for("login"))
    history = database.get_recent_messages()   # load old messages
    return render_template("chat.html", username=session["username"], history=[dict(r) for r in history])


# TEMPORARY: lets us test chat history without WebSockets.
# Dev's real-time code will replace this.
@app.route("/send", methods=["POST"])
def send():
    if "username" not in session:
        return redirect(url_for("login"))
    text = request.form["message"].strip()
    if text:
        database.save_message(session["username"], text)
    return redirect(url_for("chat"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    realtime.run(app)
