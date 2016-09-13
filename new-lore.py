#!/usr/bin/env python3

# Gets latest lore

import argparse
from peewee import peewee
# from loremodels import Lore

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
    parser.add_argument('-n', '--num', help="number of lore to return",
                        type=int, default=10)
    args = parser.parse_args()

    for lore in reversed(
            Lore.select().order_by(Lore.time.desc()).limit(args.num)):
        print(lore, '\n')


if __name__ == "__main__":
    main()
