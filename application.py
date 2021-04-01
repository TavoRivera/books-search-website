import os
import string
import requests
import json

from flask import Flask, flash, session, render_template, redirect, request, url_for, jsonify
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
    if session.get("logged_in"):
        return render_template("index.html", name=session["user_name"])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        print(request.form.get("password"))
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
        session["user_name"] = result[1]
        session["logged_in"] = True

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
    # ingreso user y pass y compruebo
    if request.method == "POST":

        user = request.form.get("username")
        pass1 = request.form.get("password")
        pass2 = request.form.get("confirmation")

        if len(pass1) < 4:
            return render_template("register.html", alert="ingrese contraseña de al menos cuatro caracteres")
        if not user:
            return render_template("register.html", alert="ingrese un nombre de usuario")
        elif not pass1:
            return render_template("register.html", alert="ingrese una contraseña")
        elif pass1 != pass2:
            return render_template("register.html", alert="contraseñas no coinciden")
        # busco en mi base de datos si ese usuario ya existe
        new = db.execute(
            "SELECT * FROM users WHERE username = :username;", {"username": user}).fetchone()
        # si no hay usuarios con ese nombre, inserto este nombre de usuario a la tabla users
        if new is None:
            db.execute("INSERT INTO users (username, hash) VALUES (:user ,:pass1);", {
                       "user": user, "pass1": generate_password_hash(pass1)})
            db.commit()
            return render_template("login.html", success="Registrado")
        else:
            return render_template("register.html", alert="Usuario ya existe")
    else:
        return render_template("register.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():

    # Get form information
    if request.method == "POST":
        # capwords para que cada inicio de una palabra inicie con mayúscula para mejorar la búsqueda
        search = str(request.form.get("search"))
        search = string.capwords(search, sep=None)
        # busca si ese libro existe o si hay algún parecido
        query = db.execute(
            "SELECT * FROM books WHERE title LIKE :search OR isbn LIKE :search OR author LIKE :search", {
                "search": '%' + search + '%'},
        )
        books = query.fetchall()
        # si el tamaño de la búsqueda es 0, entonces no encontró resultados
        if len(books) == 0:
            return render_template("index.html", alert="libro no encotrado")
        return render_template("index.html", name=session["user_name"], books=books)


@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):

    user = session["user_id"]
    # seleccionar de la tabla books el isbn
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn})
    book_id = book.fetchone()
    book_id = book_id[0]
    # seleccionar información de books correspondiente a su isbn
    row = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn",
                     {"isbn": isbn})
    book_info = row.fetchall()
    # toma el nombre de usuario, comentario, putuación y fecha de las tablas users y rate cuando está en un libro específico
    rev = db.execute(
        "SELECT username, comment, rating, time FROM users JOIN rate ON users.id_user = rate.id_user WHERE isbn = :isbn", {"isbn": isbn})
    reviews = rev.fetchall()
    # solicitud al api para tomar información
    res = requests.get(
        "https://www.googleapis.com/books/v1/volumes/?q=isbn:"+isbn)
    data = res.json()

    if request.method == "POST":

        rating = int(request.form.get("rating"))
        comment = request.form.get("comment")
        # comprueba si el usuario ya hizo un comentario
        comprobe = db.execute("SELECT * FROM rate WHERE id_user = :id_user AND isbn = :id_book",
                              {"id_user": user,
                               "id_book": book_id})

        if comprobe.rowcount == 1:
            return render_template("book.html", book_info=book_info, rate=reviews, alert="Ya subiste una opinión sobre este libro")
        # si no ha hecho un comentario, inserta el nuevo
        db.execute("INSERT INTO rate (isbn, id_user, rating, comment, time) VALUES (:isbn, :id_user, :rating, :comment, now())", {
                   "isbn": book_id, "id_user": user, "rating": rating, "comment": comment})
        db.commit()
        # extraemos la informacion de la api
        xd = data["items"][0]
        description = xd["volumeInfo"]["description"]
        categories = xd["volumeInfo"]["categories"]
        rated = xd["volumeInfo"]["averageRating"]
        # el comentario no se coloca automáticamente, por lo que habrá que recargar luego del submit
        return render_template("book.html", rate=reviews, book_info=book_info, description=description, categories=categories, rated=rated, success="has añadido un comentario, recarga la página para poder verlo")

    else:
        # extraemos la información de la api otra vez
        xd = data["items"][0]
        description = xd["volumeInfo"]["description"]
        categories = xd["volumeInfo"]["categories"]
        rated = xd["volumeInfo"]["averageRating"]

        return render_template("book.html", rate=reviews, book_info=book_info, description=description, categories=categories, rated=rated)


@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):
    # se selecciona la información del libro cuando se introduzca su isbn
    lookForBook = db.execute(
        "SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if not lookForBook:
        return jsonify({"error": "Invalid ISBN"}), 422
    # aolicitud al api

    res = requests.get(
        "https://www.googleapis.com/books/v1/volumes/?q=isbn:"+isbn)
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    # se toma información del api
    xd = data["items"][0]
    averageRating = xd["volumeInfo"]["averageRating"]
    count = xd["volumeInfo"]["ratingsCount"]

    # Return results in JSON format
    return jsonify({
        "title": lookForBook.title,
        "author": lookForBook.author,
        "year": lookForBook.year,
        "isbn": lookForBook.isbn,
        "review_count": count,
        "average_score": averageRating
    })


def errorhandler(e):
    """Handle error"""
    return (e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
