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

    def __str__(self):
        return "[%s] [%s]\n%s" % (self.time, self.author, self.lore)


def main():
    lore_file = 'lore.db'
    db.init(lore_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('lore', nargs='+', help="blob of lore to save")
    args = parser.parse_args()
    lore = ' '.join(args.lore)

    # add-lore "[mike_bloomfield]: how do i use the lorebot "

    t = datetime.datetime.now()

    # Try to parse plain loreblob, extracting author from []
    author = lore.split(': ')[0].split('[')[1].split(']')[0]
    loretxt = ': '.join(lore.split(': ')[1:])

    db.begin()
    # Check to see if lore already exists (based on author/lore match)
    matches = Lore.select().where(Lore.author == author and Lore.lore == lore).count()
    if matches == 0:
        l = Lore.create(time=t, author=author, lore=loretxt, rating=0)
        print(l)
    else:
        print("Lore already exists...")
    db.commit()


if __name__ == "__main__":
    main()
