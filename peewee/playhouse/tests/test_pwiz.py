import datetime
import os
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import textwrap
import sys

from peewee import *
from pwiz import *
from playhouse.tests.base import database_initializer
from playhouse.tests.base import mock
from playhouse.tests.base import PeeweeTestCase
from playhouse.tests.base import skip_if


db = database_initializer.get_database('sqlite')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(primary_key=True)
    id = IntegerField(default=0)

class Note(BaseModel):
    user = ForeignKeyField(User)
    text = TextField(index=True)
    data = IntegerField(default=0)
    misc = IntegerField(default=0)

    class Meta:
        indexes = (
            (('user', 'text'), True),
            (('user', 'data', 'misc'), False),
        )

class Category(BaseModel):
    name = CharField(unique=True)
    parent = ForeignKeyField('self', null=True)

class OddColumnNames(BaseModel):
    spaces = CharField(db_column='s p aces')
    symbols = CharField(db_column='w/-nug!')

class capture_output(object):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._buffer = StringIO()
        return self

    def __exit__(self, *args):
        self.data = self._buffer.getvalue()
        sys.stdout = self._stdout

EXPECTED = """
from peewee import *

database = SqliteDatabase('/tmp/peewee_test.db', **{})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Category(BaseModel):
    name = CharField(unique=True)
    parent = ForeignKeyField(db_column='parent_id', null=True, rel_model='self', to_field='id')

    class Meta:
        db_table = 'category'

class User(BaseModel):
    id = IntegerField()
    username = CharField(primary_key=True)

    class Meta:
        db_table = 'user'

class Note(BaseModel):
    data = IntegerField()
    misc = IntegerField()
    text = TextField(index=True)
    user = ForeignKeyField(db_column='user_id', rel_model=User, to_field='username')

    class Meta:
        db_table = 'note'
        indexes = (
            (('user', 'data', 'misc'), False),
            (('user', 'text'), True),
        )
""".strip()


EXPECTED_ORDERED = """
from peewee import *

database = SqliteDatabase('/tmp/peewee_test.db', **{})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class User(BaseModel):
    username = CharField(primary_key=True)
    id = IntegerField()

    class Meta:
        db_table = 'user'

class Note(BaseModel):
    user = ForeignKeyField(db_column='user_id', rel_model=User, to_field='username')
    text = TextField(index=True)
    data = IntegerField()
    misc = IntegerField()

    class Meta:
        db_table = 'note'
        indexes = (
            (('user', 'data', 'misc'), False),
            (('user', 'text'), True),
        )
""".strip()


class BasePwizTestCase(PeeweeTestCase):
    models = []

    def setUp(self):
        super(BasePwizTestCase, self).setUp()
        if os.path.exists(db.database):
            os.unlink(db.database)
        db.connect()
        db.create_tables(self.models)
        self.introspector = Introspector.from_database(db)

    def tearDown(self):
        super(BasePwizTestCase, self).tearDown()
        db.drop_tables(self.models)
        db.close()


class TestPwiz(BasePwizTestCase):
    models = [User, Note, Category]

    def test_print_models(self):
        with capture_output() as output:
            print_models(self.introspector)

        self.assertEqual(output.data.strip(), EXPECTED)

    def test_print_header(self):
        cmdline = '-i -e sqlite %s' % db.database

        with capture_output() as output:
            with mock.patch('pwiz.datetime.datetime') as mock_datetime:
                now = mock_datetime.now.return_value
                now.strftime.return_value = 'February 03, 2015 15:30PM'
                print_header(cmdline, self.introspector)

        self.assertEqual(output.data.strip(), (
            '# Code generated by:\n'
            '# python -m pwiz %s\n'
            '# Date: February 03, 2015 15:30PM\n'
            '# Database: %s\n'
            '# Peewee version: %s') % (cmdline, db.database, peewee_version))


@skip_if(lambda: sys.version_info[:2] < (2, 7))
class TestPwizOrdered(BasePwizTestCase):
    models = [User, Note]

    def test_ordered_columns(self):
        with capture_output() as output:
            print_models(self.introspector, preserve_order=True)

        self.assertEqual(output.data.strip(), EXPECTED_ORDERED)


class TestPwizInvalidColumns(BasePwizTestCase):
    models = [OddColumnNames]

    def test_invalid_columns(self):
        with capture_output() as output:
            print_models(self.introspector)

        result = output.data.strip()
        expected = textwrap.dedent("""
            class Oddcolumnnames(BaseModel):
                s_p_aces = CharField(db_column='s p aces')
                w_nug_ = CharField(db_column='w/-nug!')

                class Meta:
                    db_table = 'oddcolumnnames'""").strip()

        actual = result[-len(expected):]
        self.assertEqual(actual, expected)
