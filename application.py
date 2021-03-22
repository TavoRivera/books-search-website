import os

from flask import Flask, flash, session, render_template, redirect, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)


# asegurar que no quede almacenado en caché
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Check for environment variable
if not "postgres://quextkykixqbuo: 5eae6fe7806d24b11d794730f2bfd0650e0a8b93e9f990b5b0126fe10fa8c170@ec2-54-145-102-149.compute-1.amazonaws.com: 5432/d1mic7vjgdmk59":
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(
    "postgres://quextkykixqbuo:5eae6fe7806d24b11d794730f2bfd0650e0a8b93e9f990b5b0126fe10fa8c170@ec2-54-145-102-149.compute-1.amazonaws.com:5432/d1mic7vjgdmk59")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():

    return render_template("index.html", name="Noe")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", alert="proporcione un nombre de usuario")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", alert="proporcione una contraseña")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username;",
                          {"username": request.form.get("username")})
        result = rows.fetchone()

        # Ensure username exists and password is correct
        if result == None or not check_password_hash(result[2], request.form.get("password")):
            return render_template("login.html", alert="usuario o contraseña inválidos")

        # Remember which user has logged in
        session["user_id"] = result[0]

        # Redirect user to home page
        return render_template("index.html", name=result[1])

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        user = request.form.get("username")
        pass1 = request.form.get("password")
        pass2 = request.form.get("confirmation")

        if len(pass1) < 4:
            return render_template("register.html", alert="ingrese contraseña de al menos cuatro caracteres")
        if not user:
            return render_template("register.html", alert="ingrese un nombre de usuario")
        elif not pass1:
            return render_template("register.html", alert="ingrese una cotraseña")
        elif pass1 != pass2:
            return render_template("register.html", alert="contraseñas no coinciden")

        new = db.execute(
            "SELECT * FROM users WHERE username = :username;", {"username": user}).fetchone()

        if new is None:
            db.execute("INSERT INTO users (username, hash) VALUES (:user ,:pass1);", {
                       "user": user, "pass1": generate_password_hash(pass1)})
            db.commit()
            return render_template("login.html", success="Registrado de pana")
        else:
            return render_template("register.html", alert="Usuario ya existe")
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    return (e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
