import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not "postgres://abufijpcbmrzyy: 476bd1f084e98588a1a582ab3b5e60f9582ef9d0369fcfd18def88ce0e53601a@ec2-18-204-101-137.compute-1.amazonaws.com: 5432/d7dul6fssepujq":
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = "postgres://abufijpcbmrzyy: 476bd1f084e98588a1a582ab3b5e60f9582ef9d0369fcfd18def88ce0e53601a@ec2-18-204-101-137.compute-1.amazonaws.com: 5432/d7dul6fssepujq"
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Project 1: TODO"
