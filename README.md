# Lore Database

This is a collection of utilities for managing and perusing a database of lore.

## Importing lore

To import existing lore, first make sure it is in the following CSV format: `date|author|text`

`date` will be parsed by the Python `dateutil` library, which is generally very forgiving.

For multi-line text, enclose them in double-quotes (`"`).

Then, import the lore:

`python import-lore.py lore.csv`

## Adding lore

    usage: add-lore.py [-h] author lore [lore ...]

    positional arguments:
    author
    lore        blob of lore to save

You can pass the lore either in quotes, or as plain text.
add-lore.py will try to capture all of the remaining arguments as lore.

## Inspecting lore

`python new-lore.py [-n 10]`

By default will show then last 10 pieces of lore. `-n` specifies how many pieces to return.

`python random-lore.py`

Will show one random piece of lore.

## Searching lore

`python search-lore.py [-a] pattern`

`-a` specifies you want to search by the author field

## Dumping lore to text file

`python dump-lore.py output_file`

This writes the lore to the `output_file`. Suitable for serving via the web, if desired.
