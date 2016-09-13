#!/usr/bin/env python3

# Gets latest lore

import argparse
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
    parser.add_argument('output_file', help="file to write lore to")
    args = parser.parse_args()

    with open(args.output_file, 'w') as f:
        for lore in reversed(
                Lore.select().order_by(Lore.time.desc())):
            print(lore, file=f)
            print("", file=f)


if __name__ == "__main__":
    main()
