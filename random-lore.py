#!/usr/bin/env python3

import random
import sys

import argparse
import datetime
from peewee import peewee
from loremodels import Lore

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
    parser.add_argument("pattern", help="plain text pattern to filter lore on", default="")
    args = parser.parse_args()

    lore = Lore.select().where(Lore.lore.contains(args.pattern)).order_by(peewee.fn.Random()).limit(1)
    for l in lore:
        print(l)


if __name__ == "__main__":
    main()
