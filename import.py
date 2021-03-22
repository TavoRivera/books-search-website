import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(
    "postgres://quextkykixqbuo:5eae6fe7806d24b11d794730f2bfd0650e0a8b93e9f990b5b0126fe10fa8c170@ec2-54-145-102-149.compute-1.amazonaws.com:5432/d1mic7vjgdmk59")
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        print(
            f"Added in book with isbn: {isbn},  title: {title},      author: {author}       and year published: {year}")
    db.commit()


if __name__ == "__main__":
    main()
