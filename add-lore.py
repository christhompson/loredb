#!/usr/bin/env python3

import argparse
import datetime
from peewee import peewee

db = peewee.SqliteDatabase(None)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class Lore(BaseModel):
    time = peewee.DateTimeField(null=True, index=True)
    author = peewee.CharField(null=True, index=True)
    lore = peewee.CharField()
    rating = peewee.FloatField()


def main():
    lore_file = 'lore.db'
    db.init(lore_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('author')
    parser.add_argument('lore', nargs='+', help="blob of lore to save")
    args = parser.parse_args()
    print(args.lore)

    t = datetime.datetime.now()

    # Try to parse plain loreblob, extracting author from []
    author = args.author
    lore = ' '.join(args.lore)
    print(author, lore)

    db.begin()
    # Check to see if lore already exists (based on author/lore match)
    matches = Lore.select().where(Lore.author == author and Lore.lore == lore).count()
    if matches == 0:
        Lore.create(time=t, author=author, lore=lore, rating=0)
    db.commit()


if __name__ == "__main__":
    main()
