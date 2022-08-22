import os, string, requests, json

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
if not "postgresql://quextkykixqbuo: 5eae6fe7806d24b11d794730f2bfd0650e0a8b93e9f990b5b0126fe10fa8c170@ec2-54-145-102-149.compute-1.amazonaws.com: 5432/d1mic7vjgdmk59":
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgresql://quextkykixqbuo:5eae6fe7806d24b11d794730f2bfd0650e0a8b93e9f990b5b0126fe10fa8c170@ec2-54-145-102-149.compute-1.amazonaws.com:5432/d1mic7vjgdmk59")
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
            return render_template("login.html", alert="Provide an user")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", alert="Provide a password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username;",
                          {"username": request.form.get("username")})
        result = rows.fetchone()

        # Ensure username exists and password is correct
        if result == None or not check_password_hash(result[2], request.form.get("password")):
            return render_template("login.html", alert="password not match")

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
    # enter my user, pass and check
    if request.method == "POST":

        user = request.form.get("username")
        pass1 = request.form.get("password")
        pass2 = request.form.get("confirmation")

        if len(pass1) < 4:
            return render_template("register.html", alert="Enter a password with 4 or more characters")
        if not user:
            return render_template("register.html", alert="Enter an username")
        elif not pass1:
            return render_template("register.html", alert="Enter a password")
        elif pass1 != pass2:
            return render_template("register.html", alert="Passwords not match")
        # search in my db if the user exist
        new = db.execute(
            "SELECT * FROM users WHERE username = :username;", {"username": user}).fetchone()
        # if username doesn't exist, insert this username in the table users
        if new is None:
            db.execute("INSERT INTO users (username, hash) VALUES (:user ,:pass1);", {
                       "user": user, "pass1": generate_password_hash(pass1)})
            db.commit()
            return render_template("login.html", success="Register Success")
        else:
            return render_template("register.html", alert="Username already exists")
    else:
        return render_template("register.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():

    # Get form information
    if request.method == "POST":
        # capwords so that every beginning of a word starts with a capital letter to improve the search
        search = str(request.form.get("search"))
        search = string.capwords(search, sep=None)
        # search if that book exists or if there is any resemblance
        query = db.execute(
            "SELECT * FROM books WHERE title LIKE :search OR isbn LIKE :search OR author LIKE :search", {
                "search": '%' + search + '%'},
        )
        books = query.fetchall()
        # if len of search is 0, then found no results
        if len(books) == 0:
            return render_template("index.html", alert="Book not found")

        return render_template("index.html", name=session["user_name"], books=books)


@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):

    user = session["user_id"]

    # select information in the table books corresponding to your isbn
    books = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn = :isbn",
                     {"isbn": isbn})
    book_info = books.fetchall()
    # take the username, comment, rating and time of the tables users n rate when be into a specific book
    rev = db.execute(
        "SELECT username, comment, rating, time FROM users JOIN rate ON users.id_user = rate.id_user WHERE isbn = :isbn", {"isbn": isbn})
    reviews = rev.fetchall()
    # query to api for select your information
    res = requests.get(
        "https://www.googleapis.com/books/v1/volumes/?q=isbn:"+isbn)
    data = res.json()
    # exctract the information
    api = data["items"][0]
    description = api["volumeInfo"]["description"]
    categories = api["volumeInfo"]["categories"]
    rated = api["volumeInfo"]["averageRating"]
    count = api["volumeInfo"]["ratingsCount"]

    if request.method == "POST":

        rating = int(request.form.get("rating"))
        comment = request.form.get("comment")
        # check if the user already made a comment
        comprobe = db.execute("SELECT * FROM rate WHERE id_user = :id_user AND isbn = :id_book",
                              {"id_user": user,
                               "id_book": isbn})

        if comprobe.rowcount == 1:
            return render_template("book.html", book_info=book_info, rate=reviews, alert="Already You submit a comment for this book")
        # if you have not made a comment, insert the new one
        db.execute("INSERT INTO rate (isbn, id_user, rating, comment, time) VALUES (:isbn, :id_user, :rating, :comment, now())", {
                   "isbn": isbn, "id_user": user, "rating": rating, "comment": comment})
        db.commit()

        """ el comentario no se coloca automáticamente, por lo que habrá que recargar luego del submit"""
        return redirect(url_for('book',rate=reviews, book_info=book_info, description=description, categories=categories, rated=rated, count=count, isbn=isbn))
    else:
        return render_template("book.html", rate=reviews, book_info=book_info, description=description, categories=categories, rated=rated, count=count)


"""Nota: para la mayoría de los libros por no decir todos, con la api se extrae la información y la muestra en la página books, pero hay unos libros específicos que al parecer no contiene/
 esa api (por ejemplo The 100) y retora un error de indice "item", que si trato de repararlo tendría que quitar la información de la api en la página book y perdería la parte bonita de la api"""


@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):
    # book information is selected when you enter your isbn
    books = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn})
    book_info = books.fetchone()
    if not book_info:
        return jsonify({"error": "Invalid ISBN"}), 400
    # query api
    res = requests.get(
        "https://www.googleapis.com/books/v1/volumes/?q=isbn:"+isbn)
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    # se toma información del api
    api = data["items"][0]
    averageRating = api["volumeInfo"]["averageRating"]
    count = api["volumeInfo"]["ratingsCount"]

    # Return results in JSON format
    return jsonify({
        "title": book_info.title,
        "author": book_info.author,
        "year": book_info.year,
        "isbn": book_info.isbn,
        "review_count": count,
        "average_score": averageRating
    })


def errorhandler(e):
    """Handle error"""
    return (e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
