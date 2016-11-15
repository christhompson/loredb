#!/usr/bin/env python3

import peewee
from playhouse.migrate import *

db = SqliteDatabase('lore.db')
migrator = SqliteMigrator(db)

upvote_field = IntegerField(null=False, default=4)
downvote_field = IntegerField(null=False, default=10)

migrate(
    migrator.add_column(table, 'upvotes', upvote_field)
    migrator.add_column(table, 'downvotes', downvote_field)
    migrator.drop_column(table, 'rating')
)
