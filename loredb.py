#!/usr/bin/env python3

'''loredb.py

A tool for managing and querying a database of lore.
'''

import argparse
import datetime
import csv
import sys
import peewee


def compute_rating(upvotes, downvotes):
    return upvotes / (upvotes + downvotes)


class BaseModel(peewee.Model):
    class Meta:
        database = peewee.SqliteDatabase(None)


class Lore(BaseModel):
    # Lore details
    time = peewee.DateTimeField(null=True, index=True)
    author = peewee.CharField(null=True, index=True)
    lore = peewee.CharField()

    # Bayesian priors for voting
    fake_upvotes = 4
    fake_downvotes = 10

    # Voting
    upvotes = peewee.IntegerField(null=False, default=fake_upvotes)
    downvotes = peewee.IntegerField(null=False, default=fake_downvotes)
    rating = peewee.FloatField(null=False,
                               default=compute_rating(fake_upvotes,
                                                      fake_downvotes),
                               index=True)

    def __str__(self):
        return "[#%d] [%s] [rating: %.3f] [%s]\n%s" % (
            self.id, self.time, self.rating, self.author, self.lore)


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
    delete_parser.add_argument('id', help='id of lore to delete', type=int)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument('id', help='id of lore to update', type=int)
    update_parser.add_argument('author', help='author of the lore')
    update_parser.add_argument('lore', help='text of the lore')

    upvote_parser = subparsers.add_parser("upvote")
    upvote_parser.add_argument('id', help='id of lore to upvote', type=int)

    downvote_parser = subparsers.add_parser("downvote")
    downvote_parser.add_argument(
        'id', help='id of lore to downvote', type=int)

    best_parser = subparsers.add_parser("best")
    best_parser.add_argument('-n', '--num', help='number of lore to return',
                             type=int, default=10)

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
        delete(args.id)
    elif args.command == "update":
        update(args.id, args.author, args.lore)
    elif args.command == "upvote":
        vote(args.id, which='up')
    elif args.command == "downvote":
        vote(args.id, which='down')
    elif args.command == "best":
        best(num=args.num)
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
        l = Lore.create(time=now, author=author, lore=lore)
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
            Lore.create(time=t, author=author, lore=lore)


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


def best(num=10):
    for lore in Lore.select().order_by(Lore.rating.desc()).limit(num):
        print(lore, '\n')


def delete(id):
    try:
        l = Lore.get(Lore.id == id)
    except peewee.DoesNotExist as err:
        print("Invalid id:", err)
        sys.exit(1)

    rows_deleted = l.delete_instance()
    print("Deleted %d lores" % rows_deleted)


def update(id, author, lore):
    try:
        l = Lore.get(Lore.id == id)
    except peewee.DoesNotExist as err:
        print("Invalid id:", err)
        sys.exit(1)

    l.author = author
    l.lore = lore
    l.save()
    print("Lore updated")


def vote(id, which='up'):
    try:
        l = Lore.get(Lore.id == id)
    except peewee.DoesNotExist as err:
        print("Invalid id:", err)
        sys.exit(1)

    if which == 'up':
        l.upvotes += 1
    elif which == 'down':
        l.downvotes += 1
    else:
        print("Invalid voting requested:", which)
        sys.exit(1)
    # Update the lore rating
    l.rating = compute_rating(l.upvotes, l.downvotes)
    l.save()
    print("Lore updated")


if __name__ == "__main__":
    main()
