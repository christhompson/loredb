#!/usr/bin/env python3

'''loredb.py

A tool for managing and querying a database of lore.
'''

import argparse
import datetime
import csv
import sys
import peewee
from playhouse.fields import ManyToManyField


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
        return "[#%d] [%s] [rating: %.3f] [%s]\nTags: %s\n%s" % (
            self.id, self.time, self.rating, self.author,
            ', '.join([str(tag) for tag in self.tags]),
            self.lore)


class Tag(BaseModel):
    name = peewee.CharField(index=True)
    lores = ManyToManyField(Lore, related_name="tags")

    def __str__(self):
        return self.name


LoreTag = Tag.lores.get_through_model()


def main():
    lore_file = 'lore.db'
    db = BaseModel._meta.database
    db.init(lore_file)

    main_parser = argparse.ArgumentParser(description='Handle your lore')
    subparsers = main_parser.add_subparsers(title='subcommands',
                                            dest='command')

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('author')
    add_parser.add_argument('lore', nargs='+', help='blob of lore to save')
    add_parser.set_defaults(func=_add)

    new_parser = subparsers.add_parser('new')
    new_parser.add_argument('-n', '--num', help='number of lore to return',
                            type=int, default=10)
    new_parser.set_defaults(func=_new)

    dump_parser = subparsers.add_parser('dump')
    dump_parser.add_argument('output_file', help='file to write lore to')
    dump_parser.set_defaults(func=_dump)

    search_parser = subparsers.add_parser('search')
    search_parser.add_argument('-a', '--author',
                               help='search on author instead',
                               default=False, action='store_true')
    search_parser.add_argument('-n', '--num', help='number of lore to return',
                               type=int, default=10)
    search_parser.add_argument('pattern')
    search_parser.set_defaults(func=_search)

    import_parser = subparsers.add_parser('import')
    import_parser.add_argument('old_lore', help='csv file of old lore')
    import_parser.set_defaults(func=_import_lore)

    random_parser = subparsers.add_parser('random')
    random_parser.add_argument('pattern', nargs='*',
                               help='plain text pattern to filter lore on')
    random_parser.add_argument('-n', '--num', help='number of lore to return',
                               type=int, default=1)
    random_parser.set_defaults(func=_random)

    top_parser = subparsers.add_parser('top')
    top_parser.add_argument('-n', '--num', help='limit number of loremasters',
                            type=int, default=10)
    top_parser.set_defaults(func=_top)

    delete_parser = subparsers.add_parser('delete')
    delete_parser.add_argument('id', help='id of lore to delete', type=int)
    delete_parser.set_defaults(func=_delete)

    update_parser = subparsers.add_parser('update')
    update_parser.add_argument('id', help='id of lore to update', type=int)
    update_parser.add_argument('author', help='author of the lore')
    update_parser.add_argument('lore', help='text of the lore')
    update_parser.set_defaults(func=_update)

    upvote_parser = subparsers.add_parser('upvote')
    upvote_parser.add_argument('id', nargs='+', type=int,
                               help='id of lore(s) to upvote')
    upvote_parser.set_defaults(func=_upvote)

    downvote_parser = subparsers.add_parser('downvote')
    downvote_parser.add_argument('id', nargs='+', type=int,
                                 help='id of lore to downvote')
    downvote_parser.set_defaults(func=_downvote)

    best_parser = subparsers.add_parser('best')
    best_parser.add_argument('-n', '--num', help='number of lore to return',
                             type=int, default=10)
    best_parser.set_defaults(func=_best)

    tag_parser = subparsers.add_parser('tag')
    tag_parser.add_argument('id', type=int, help='id of lore to tag')
    tag_parser.add_argument('tags', nargs='+', help='tags to apply to lore')
    tag_parser.set_defaults(func=_add_tags)

    get_tag_parser = subparsers.add_parser('get-tag')
    get_tag_parser.add_argument('tag', help='get lores matching this tag')
    get_tag_parser.add_argument('-n', '--num', help='number of lore to return',
                                type=int, default=10)
    get_tag_parser.set_defaults(func=_get_tag)

    remove_tag_parser = subparsers.add_parser('delete-tag')
    remove_tag_parser.add_argument('id', type=int,
                                   help='id of lore to remove tag from')
    remove_tag_parser.add_argument('tag', help='tag to remove')
    remove_tag_parser.set_defaults(func=_remove_tag)

    # Parse the args and call whatever function was selected
    args = main_parser.parse_args()
    if args.command is None:
        main_parser.print_help()
        sys.exit(1)
    else:
        args.func(args)
        sys.exit(0)


def _add(args):
    add(args.author, args.lore)


def add(author, lore):
    now = datetime.datetime.now()
    lore = ' '.join(lore)
    lore, created = Lore.get_or_create(
        author=author, lore=lore, defaults={'time': now})
    if not created:
        upvote([lore.id])


def _new(args):
    new(num=args.num)


def new(num=10):
    for lore in reversed(
            Lore.select().order_by(Lore.time.desc()).limit(num)):
        print(lore, '\n')


def _dump(args):
    dump(args.output_file)


def dump(output_file):
    with open(output_file, 'w') as f:
        for lore in reversed(
                Lore.select().order_by(Lore.time.desc())):
            print(lore, file=f)
            print("", file=f)


def _search(args):
    search(args.pattern, author=args.author, num=args.num)


def search(pattern, author=False, num=10):
    if author:
        lores = Lore.select().where(Lore.author.contains(pattern))
    else:
        lores = Lore.select().where(Lore.lore.contains(pattern))
    lores = lores.order_by(Lore.time.desc()).limit(num)

    for lore in reversed(lores):
        print(lore, '\n')


def _import_lore(args):
    import_lore(args.old_lore)


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


def _random(args):
    random(pattern=args.pattern, num=args.num)


def random(pattern=None, num=1):
    if pattern is None:
        pattern = []
    pattern = ' '.join(pattern)
    lore = Lore.select().where(
        Lore.lore.contains(pattern)).order_by(peewee.fn.Random()).limit(num)
    for l in lore:
        print(l, '\n')


def _top(args):
    top(num=args.num)


def top(num=10):
    lores = get_top_lore(num)

    col1_size = max(max(len(l.author) for l in lores), len("Author"))
    col2_size = max(max(len(str(l.count)) for l in lores), len("# Lore"))
    col3_size = max(max(len("{:.3f}".format(l.total)) for l in lores),
                    len("Score"))

    pretty_print_fmt = "{:{size1}}\t{:>{size2}}\t{:>{size3}}"
    print(pretty_print_fmt.format(
        "AUTHOR", "# LORE", "SCORE",
        size1=col1_size, size2=col2_size, size3=col3_size
    ))
    for lore in lores:
        if lore.author == "":
            lore.author = "[blank]"
        print(pretty_print_fmt.format(
            lore.author, lore.count, "{:.3f}".format(lore.total),
            size1=col1_size, size2=col2_size, size3=col3_size
        ))


def get_top_lore(num=10):
        # Order authors by Sum(rating), dropping downvoted lores.
    cutoff_rating = 4.0 / 16.0  # Downvoted >= 2 times
    return Lore.select(Lore.author,
                       peewee.fn.Count(Lore.id).alias('count'),
                       peewee.fn.Sum(Lore.rating).alias('total')).\
        where(Lore.rating > cutoff_rating).\
        group_by(peewee.fn.Lower(Lore.author)).\
        order_by(peewee.fn.Sum(Lore.rating).desc()).\
        limit(num)


def _best(args):
    best(num=args.num)


def best(num=10):
    for lore in Lore.select().order_by(Lore.rating.desc()).limit(num):
        print(lore, '\n')


def _delete(args):
    delete(args.id)


def delete(lore_id):
    try:
        l = Lore.get(Lore.id == lore_id)
    except peewee.DoesNotExist as err:
        print("Invalid id:", err)
        sys.exit(1)

    rows_deleted = l.delete_instance()
    print("Deleted %d lores" % rows_deleted)


def _update(args):
    update(args.id, args.author, args.lore)


def update(lore_id, author, lore):
    try:
        l = Lore.get(Lore.id == lore_id)
    except peewee.DoesNotExist as err:
        print("Invalid id:", err)
        sys.exit(1)

    l.author = author
    l.lore = lore
    l.save()
    print("Lore updated")


def _upvote(args):
    upvote(args.id)


def upvote(lore_ids):
    for lore_id in lore_ids:
        try:
            l = Lore.get(Lore.id == lore_id)
        except peewee.DoesNotExist as err:
            print("Invalid id:", err)
            sys.exit(1)
        l.upvotes += 1
        print("Lore upvoted")
        # Update the lore rating
        l.rating = compute_rating(l.upvotes, l.downvotes)
        l.save()


def _downvote(args):
    downvote(args.id)


def downvote(ids):
    for id in ids:
        try:
            l = Lore.get(Lore.id == id)
        except peewee.DoesNotExist as err:
            print("Invalid id:", err)
            sys.exit(1)
        l.downvotes += 1
        print("Lore downvoted")
        # Update the lore rating
        l.rating = compute_rating(l.upvotes, l.downvotes)
        l.save()


def _add_tags(args):
    add_tags(args.id, args.tags)


def add_tags(lore_id, tags):
    try:
        l = Lore.get(Lore.id == lore_id)
    except peewee.DoesNotExist as err:
        print("Invalid id:", err)
        sys.exit(1)
    for tag in tags:
        tag, _ = Tag.get_or_create(name=tag)
        if tag not in l.tags:
            l.tags.add(tag)


def _get_tag(args):
    get_tag(args.tag, num=args.num)


def get_tag(tag, num=10):
    try:
        t = Tag.get(Tag.name == tag)
    except peewee.DoesNotExist as err:
        print("No lore with that tag", err)
        sys.exit(1)
    for lore in t.lores.limit(num):
        print(lore, '\n')


def _remove_tag(args):
    remove_tag(args.id, args.tag)


def remove_tag(lore_id, tag):
    try:
        l = Lore.get(Lore.id == lore_id)
        t = Tag.get(Tag.name == tag)
    except peewee.DoesNotExist as err:
        print("Invalid id or tag:", err)
        sys.exit(1)
    l.tags.remove(t)


if __name__ == "__main__":
    main()
