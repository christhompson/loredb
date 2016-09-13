#!/usr/bin/env python3

import csv
from dateutil import parser
from peewee import peewee
from loremodels import Lore

db = peewee.SqliteDatabase(None)


def main():
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument('old_lore', help="csv file of old lore")
    args = argparser.parse_args()
    print(args.old_lore)

    lore_file = 'lore.db'
    db.init(lore_file)

    try:
        Lore.create_table()
    except peewee.OperationalError:
        print("Lore table already exists")

    with open(args.old_lore, newline='') as f:
        reader = csv.reader(f, delimiter='|')
        for row in reader:
            # print(row)
            t_str = row[0]
            author = row[1]
            lore = row[2]
            try:
                # 'Mon Sep 12 15:21:27 EDT 2016'
                t = parser.parse(t_str)
            except:
                t = None
            Lore.create(time=t, author=author, lore=lore, rating=0)


if __name__ == "__main__":
    main()
