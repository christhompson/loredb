#!/usr/bin/env python3

# loredb commands

import argparse
import datetime
import csv
import sys
from dateutil import parser
import peewee

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

    parser = argparse.ArgumentParser(description='Handle your lore')
    subparsers = parser.add_subparsers(title='subcommands',
                                       dest='command')

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument('author')
    add_parser.add_argument('lore', nargs='+', help="blob of lore to save")

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument('-n', '--num', help="number of lore to return",
                            type=int, default=10)

    dump_parser = subparsers.add_parser("dump")
    dump_parser.add_argument('output_file', help="file to write lore to")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument('-a', '--author',
                               help="search on author instead",
                               default=False, action='store_true')
    search_parser.add_argument('-n', '--num', help="number of lore to return",
                               type=int, default=10)
    search_parser.add_argument('pattern')

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument('old_lore', help="csv file of old lore")

    random_parser = subparsers.add_parser("random")
    random_parser.add_argument("pattern", nargs='*',
                               help="plain text pattern to filter lore on")

    # Parse the args and call whatever function was selected
    args = parser.parse_args()

    if args.command == "add":
        add(db, args)
    elif args.command == "new":
        new(db, args)
    elif args.command == "dump":
        dump(db, args)
    elif args.command == "search":
        search(db, args)
    elif args.command == "import":
        import_lore(db, args)
    elif args.command == "random":
        random(db, args)
    else:
        parser.print_help()
        sys.exit(1)
    sys.exit(0)


def add(db, args):
    t = datetime.datetime.now()

    # Try to parse plain loreblob, extracting author from []
    author = args.author
    lore = ' '.join(args.lore)

    db.begin()
    # Check to see if lore already exists (based on author/lore match)
    matches = Lore.select().where(
        Lore.author == author and Lore.lore == lore).count()
    if matches == 0:
        l = Lore.create(time=t, author=author, lore=lore, rating=0)
        print(l)
    else:
        print("Lore already exists...")
    db.commit()


def new(db, args):
    for lore in reversed(
            Lore.select().order_by(Lore.time.desc()).limit(args.num)):
        print(lore, '\n')


def dump(db, args):
    with open(args.output_file, 'w') as f:
        for lore in reversed(
                Lore.select().order_by(Lore.time.desc())):
            print(lore, file=f)
            print("", file=f)


def search(db, args):
    if args.author:
        lores = Lore.select().where(Lore.author.contains(args.pattern))
    else:
        lores = Lore.select().where(Lore.lore.contains(args.pattern))
    lores = lores.order_by(Lore.time.desc()).limit(args.num)

    for lore in reversed(lores):
        print(lore, '\n')


def import_lore(db, args):
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


def random(db, args):
    pattern = ' '.join(args.pattern)
    lore = Lore.select().where(
        Lore.lore.contains(pattern)).order_by(peewee.fn.Random()).limit(1)
    for l in lore:
        print(l, '\n')


if __name__ == "__main__":
    main()
