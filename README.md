# Lore Database

This is a collection of utilities for managing and perusing a database of lore.

Lore funcionality is split into a set of subcommands:

 - `add`
 - `new`
 - `top`
 - `dump`
 - `search`
 - `import`
 - `random`

## Adding lore

    usage: loredb.py add [-h] author lore [lore ...]

    positional arguments:
    author
    lore        blob of lore to save

You can pass the lore either in quotes, or as plain text.
`add` will try to capture all of the remaining arguments as lore.


## Importing lore

To import existing lore, first make sure it is in the following CSV format: `date|author|text`

`date` will be parsed by the Python `dateutil` library, which is generally very forgiving.

For multi-line text, enclose them in double-quotes (`"`).

Then, import the lore:

`loredb.py import lore.csv`

## Inspecting lore

`loredb new [-h] [-n NUM]`

By default will show then last 10 pieces of lore. `-n` specifies how many pieces to return.

`loredb top [-h] [-n NUM]`

Will show a list of the top loremasters, and the count of their lore.
By default will show the top 10.
`-n` specifies the limit on the number of loremasters.

`loredb.py random [pattern]`

Will show one random piece of lore, optionally matching `pattern`.

## Searching lore

`loredb.py search [-a] pattern`

This will search the lore for `pattern`. `-a` specifies you want to search by the author field instead of the lore field.

## Dumping lore to text file

`loredb.py dump output_file`

This writes the lore to the `output_file`. Suitable for serving via the web, if desired.

