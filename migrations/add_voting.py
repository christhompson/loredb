#!/usr/bin/env python3

import peewee
from playhouse.migrate import SqliteMigrator, migrate
from loredb import BaseModel, Lore, compute_rating

lore_file = 'lore.db'
db = BaseModel._meta.database
db.init(lore_file)

table = 'Lore'
migrator = SqliteMigrator(db)

upvote_field = peewee.IntegerField(null=False, default=4)
downvote_field = peewee.IntegerField(null=False, default=10)

migrate(
    migrator.add_column(table, 'upvotes', upvote_field),
    migrator.add_column(table, 'downvotes', downvote_field)
)

# Iterate through each row and update their rating
for lore in Lore.select():
    lore.rating = compute_rating(lore.upvotes, lore.downvotes)
    lore.save()
