#!/usr/bin/env python3

'''add-lore.py [DEPRECATED]

Script to let lorebot interface with loredb.
New uses should go directly through loredb.py.
'''

import argparse
import datetime
from loredb import BaseModel, Lore
import sys


def main():
    lore_file = 'lore.db'
    db = BaseModel._meta.database
    db.init(lore_file)

    parser = argparse.ArgumentParser()
    parser.add_argument('lore', nargs='+', help="blob of lore to save")
    args = parser.parse_args()
    lore = ' '.join(args.lore)
    now = datetime.datetime.now()

    # Try to parse plain loreblob, extracting author from []
    author = lore.split(': ')[0].split('[')[1].split(']')[0]
    loretxt = ': '.join(lore.split(': ')[1:])

    db.begin()
    # Check to see if lore already exists (based on author/lore match)
    matches = Lore.select().where(
        Lore.author == author and Lore.lore == loretxt).count()
    if matches == 0:
        Lore.create(time=now, author=author, lore=loretxt, rating=0)
        status = 0
    else:
        print("Lore already exists...")
        status = 1
    db.commit()
    sys.exit(status)


if __name__ == "__main__":
    main()
