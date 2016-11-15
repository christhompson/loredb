#!/usr/bin/env python3

'''loredb.py

A tool for managing and querying a database of lore.
'''

import argparse
import datetime
import csv
import sys
from dateutil import parser as datetime_parser
import peewee


class BaseModel(peewee.Model):
    class Meta:
        database = peewee.SqliteDatabase(None)


class Lore(BaseModel):
    time = peewee.DateTimeField(null=True, index=True)
    author = peewee.CharField(null=True, index=True)
    lore = peewee.CharField()
    upvotes = peewee.IntegerField(null=False, default=4)
    downvotes = peewee.IntegerField(null=False, default=10)

    def __str__(self):
        return "[%s] [rating: %f] [%s]\n%s" % (self.time, compute_rating(self.upvotes, self.downvotes), self.author, self.lore)


def main():
    lore_file = 'lore.db'
    db = BaseModel._meta.database
    db.init(lore_file)

    main_parser = argparse.ArgumentParser(description='Handle your lore')
    subparsers = main_parser.add_subparsers(title='subcommands',
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

    top_parser = subparsers.add_parser("top")
    top_parser.add_argument('-n', '--num', help='limit number of loremasters',
                            type=int, default=10)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument('timestamp', help='timestamp of lore to delete')

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument('timestamp', help='timestamp of lore to update')
    update_parser.add_argument('author', help='author of the lore')
    update_parser.add_argument('lore', help='text of the lore')

    upvote_parser = subparsers.add_parser("upvote")
    upvote_parser.add_argument('timestamp', help='timestamp of lore to upvote')

    downvote_parser = subparsers.add_parser("downvote")
    downvote_parser.add_argument('timestamp', help='timestamp of lore to downvote')

    # Parse the args and call whatever function was selected
    args = main_parser.parse_args()

    if args.command == "add":
        add(db, args.author, args.lore)
    elif args.command == "new":
        new(num=args.num)
    elif args.command == "dump":
        dump(args.output_file)
    elif args.command == "search":
        search(args.pattern, author=args.author, num=args.num)
    elif args.command == "import":
        import_lore(args.old_lore)
    elif args.command == "random":
        random(pattern=args.pattern)
    elif args.command == "top":
        top(num=args.num)
    elif args.command == "delete":
        delete(args.timestamp)
    elif args.command == "update":
        update(args.timestamp, args.author, args.lore)
    elif args.command == "upvote":
        upvote(args.timestamp)
    elif args.command == "downvote":
        downvote(args.timestamp)
    else:
        main_parser.print_help()
        sys.exit(1)
    sys.exit(0)


def add(db, author, lore):
    now = datetime.datetime.now()
    lore = ' '.join(lore)

    db.begin()
    # Check to see if lore already exists (based on author/lore match)
    num_matches = Lore.select().where(
        Lore.author == author and Lore.lore == lore).count()
    if num_matches == 0:
        l = Lore.create(time=now, author=author, lore=lore, rating=0)
        print(l)
    else:
        print("Lore already exists")
    db.commit()


def new(num=10):
    for lore in reversed(
            Lore.select().order_by(Lore.time.desc()).limit(num)):
        print(lore, '\n')


def dump(output_file):
    with open(output_file, 'w') as f:
        for lore in reversed(
                Lore.select().order_by(Lore.time.desc())):
            print(lore, file=f)
            print("", file=f)


def search(pattern, author=False, num=10):
    if author:
        lores = Lore.select().where(Lore.author.contains(pattern))
    else:
        lores = Lore.select().where(Lore.lore.contains(pattern))
    lores = lores.order_by(Lore.time.desc()).limit(num)

    for lore in reversed(lores):
        print(lore, '\n')


def import_lore(old_lore):
    try:
        Lore.create_table()
    except peewee.OperationalError:
        print("Lore table already exists")

    with open(old_lore, newline='') as f:
        reader = csv.reader(f, delimiter='|')
        for row in reader:
            t_str = row[0]
            author = row[1]
            lore = row[2]
            try:
                t = datetime_parser.parse(t_str)
            except ValueError:
                t = None
            Lore.create(time=t, author=author, lore=lore, rating=0)


def random(pattern=None):
    if pattern is None:
        pattern = []
    pattern = ' '.join(pattern)
    lore = Lore.select().where(
        Lore.lore.contains(pattern)).order_by(peewee.fn.Random()).limit(1)
    for l in lore:
        print(l, '\n')


def top(num=10):
    lores = Lore.select(Lore.author, peewee.fn.Count(Lore.id).alias('count')).\
        group_by(Lore.author).\
        order_by(peewee.fn.Count(Lore.id).desc()).\
        limit(num)

    col_size = max(len(l.author) for l in lores)
    for lore in lores:
        if lore.author == "":
            lore.author = "[blank]"
        print(lore.author.ljust(col_size), '\t', lore.count)


def delete(timestamp):
    try:
        t = datetime_parser.parse(timestamp)
    except ValueError as err:
        print("Invalid timestamp:", err)
        sys.exit(1)
    num = Lore.select().where(Lore.time == t).count()
    if num == 0:
        print("No lore with timestamp")
        sys.exit(1)
    if num > 1:
        print("Multiple pieces of lore matched timestamp")
        sys.exit(1)

    l = Lore.get(Lore.time == t)
    rows_deleted = l.delete_instance()
    print("Deleted %d lores" % rows_deleted)


def update(timestamp, author, lore):
    try:
        t = datetime_parser.parse(timestamp)
    except ValueError as err:
        print("Invalid timestamp:", err)
        sys.exit(1)
    num = Lore.select().where(Lore.time == t).count()
    if num == 0:
        print("No lore with timestamp")
        sys.exit(1)
    if num > 1:
        print("Multiple pieces of lore matched timestamp")
        sys.exit(1)

    l = Lore.get(Lore.time == t)
    l.author = author
    l.lore = lore
    l.save()
    print("Lore updated")


def vote(timestamp, which='up'):
    try:
        t = datetime_parser.parse(timestamp)
    except ValueError as err:
        print("Invalid timestamp:", err)
        sys.exit(1)
    num = Lore.select().where(Lore.time == t).count()
    if num == 0:
        print("No lore with timestamp")
        sys.exit(1)
    if num > 1:
        print("Multiple pieces of lore matched timestamp")
        sys.exit(1)
    
    l = Lore.get(Lore.time == t)
    if which == 'up':
        l.upvotes += 1
    elif which == 'down':
        l.downvotes += 1
    else:
        print("Invalid voting requested:", which)
        sys.exit(1)
    l.save()
    print("Lore updated")


def compute_rating(upvotes, downvotes):
    return upvotes / (upvotes + downvotes)


if __name__ == "__main__":
    main()
