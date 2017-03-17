#!/usr/bin/env python3

from loredb import BaseModel, Tag, LoreTag

lore_file = 'lore.db'
db = BaseModel._meta.database
db.init(lore_file)

db.create_tables([
    Tag,
    LoreTag
])
