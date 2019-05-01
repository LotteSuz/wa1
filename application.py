import os
import csv

from flask import Flask, session, render_template, request, redirect, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def search():
    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("search.html", books=books)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            flash("Please provide a username")

        elif not request.form.get("password"):
            flash("Please provide a password")

        elif not request.form.get("confirmation"):
            flash("Please confirm password")

        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords don't match")

        elif db.execute("SELECT * FROM users WHERE username = :username", {'username':request.form.get("username")}).rowcount == 1 :
            flash("This username is not available")

        else:
            db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                {"username":request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))})
            id = db.execute("SELECT id FROM users WHERE username = :username", {'username':request.form.get("username")}).fetchone()[0]
            session["user_id"] = id
            db.commit()
            return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login user"""
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
             flash("Provide username")

        elif not request.form.get("password"):
            flash("Provide password")

        password = db.execute("SELECT hash FROM users WHERE username = :username", {'username':request.form.get("username")}).fetchone()[0]
        if not check_password_hash(password, request.form.get("password")):
            flash("Incorrect password")

        id = db.execute("SELECT id FROM users WHERE username = :username", {'username':request.form.get("username")}).fetchone()[0]
        session["user_id"] = id
        db.commit()
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    #if request.method == "POST":
    print(f"isbn = {isbn}")
    info = db.execute("SELECT title, author, year, isbn FROM books WHERE isbn = :isbn", {'isbn': str(isbn)}).fetchall()
    print(f"info = {info}")
    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {'isbn': str(isbn)}).fetchall()
    #reviews = db.execute("SELECT ")
    # get reviews & rating
    db.commit()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "xbZVU75JQ0Vej9yLpRm2gA", "isbns": isbn})
    grdata = res.json()
    ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn", {'isbn': str(isbn)}).fetchall()
    print(f"ratingswerkt niet = {ratings}")
    amratings = len(ratings)
    if amratings == 0:
        rating = 0
    else:
        summedrates = 0
        for rating in ratings:
            summedrates += rating[0]
        if not amratings == 0:
            rating = summedrates / amratings
    return render_template("book.html", info = info, reviews = reviews, grdata = grdata, amratings = amratings, rating = rating)



@app.route("/review", methods=["POST"])
@login_required
def submit_review():
    isbn = request.form["submitbutton"]
    if db.execute("SELECT * FROM reviews WHERE userid = :id AND isbn = :isbn", {"id":session["user_id"], "isbn":isbn}).rowcount == 1:
        flash("You can submit only one review per book")

    else:
        db.execute("INSERT INTO reviews (userid, rating, review, isbn) VALUES(:userid, :rating, :review, :isbn)",
            {"userid": session["user_id"], "rating": request.form.get("rating"), "review":request.form.get("review"), "isbn":isbn})
        db.commit()
    return redirect("/")

@app.route("/api/<string:isbn>")
def book_api(isbn):
    """Return details about a single book."""

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': str(isbn)}).fetchall()
    print(f"book = {book}")
    if book is None:
        return jsonify({"error": "Invalid isbn"}), 404

    ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn", {'isbn': str(isbn)}).fetchall()
    amratings = len(ratings)
    summedrates = 0
    for rating in ratings:
        #print(f"rating = {rating}")
        summedrates += rating[0]
    if not amratings == 0:
        rating = summedrates / amratings

    return jsonify({
            "title": book[0][1],
            "author": book[0][2],
            "year": book[0][3],
            "isbn": book[0][0],
            "review_count": amratings,
            "average_score": rating
        })
