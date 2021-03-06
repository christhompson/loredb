from unittest import TestCase, main
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
from datetime import datetime, timedelta

from loredb import (BaseModel, Tag, Lore, LoreTag, compute_rating, upvote,
                    downvote, add, get_top_lore, add_tags, remove_tag)

test_db = SqliteDatabase(':memory:')
test_time = datetime.now()


def create_test_data():
    # Create some lore
    for i in range(10):
        t = test_time + timedelta(i*100)
        lore = "lore #%d" % i
        Lore.create(time=t, author=str(i), lore=lore)


class TestFunctions(TestCase):
    def test_compute_rating(self):
        upvotes = 5
        downvotes = 15
        # rating = 5 / 20
        self.assertEqual(0.25, compute_rating(upvotes, downvotes))

    def test_compute_rating_low(self):
        upvotes = 0
        downvotes = 10
        # rating = 0
        self.assertEqual(0.0, compute_rating(upvotes, downvotes))

    def test_compute_rating_high(self):
        upvotes = 100
        downvotes = 0
        self.assertEqual(1.0, compute_rating(upvotes, downvotes))

    def test_compute_rating_negative(self):
        # Vote commands only allow incrementing the integers, but nothing
        # in the database schema prevents them from going negative.
        upvotes = -1
        downvotes = 11
        self.assertEqual(-0.1, compute_rating(upvotes, downvotes))


class TestLoreVoting(TestCase):
    # Bayesian priors
    # fake_upvotes = 4
    # fake_downvotes = 10

    def test_initial_rating(self):
        # Setup
        with test_database(test_db, (BaseModel, Lore)):
            create_test_data()
            self.assertEqual(Lore.get(time=test_time).lore, "lore #0")
            self.assertEqual(Lore.get(time=test_time).rating, 4 / 14)

    def test_upvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            create_test_data()
            upvote([1])
            self.assertEqual(Lore.get(id=1).upvotes, 5)
            self.assertEqual(Lore.get(id=1).rating, 5 / 15)

    def test_downvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            create_test_data()
            downvote([1])
            self.assertEqual(Lore.get(id=1).downvotes, 11)
            self.assertEqual(Lore.get(id=1).rating, 4 / 15)

    def test_multi_upvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            create_test_data()
            upvote([1, 2])
            self.assertEqual(Lore.get(id=1).upvotes, 5)
            self.assertEqual(Lore.get(id=1).rating, 5 / 15)
            self.assertEqual(Lore.get(id=2).upvotes, 5)
            self.assertEqual(Lore.get(id=2).rating, 5 / 15)

    def test_multi_downvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            create_test_data()
            downvote([1, 2])
            self.assertEqual(Lore.get(id=1).downvotes, 11)
            self.assertEqual(Lore.get(id=1).rating, 4 / 15)
            self.assertEqual(Lore.get(id=2).downvotes, 11)
            self.assertEqual(Lore.get(id=2).rating, 4 / 15)


class TestAddLore(TestCase):
    def test_add(self):
        with test_database(test_db, (BaseModel, Lore)):
            add("bob", ["lore 1"])
            l = Lore.get(author="bob", lore="lore 1")
            self.assertGreaterEqual(l.id, 0)
            self.assertEqual(l.author, "bob")
            self.assertEqual(l.lore, "lore 1")

    def test_dupe_upvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            add("bob", ["lore"])
            add("bob", ["lore"])
            l = Lore.get(author="bob", lore="lore")
            self.assertEqual(l.upvotes, 5)


class TestTopLore(TestCase):
    def test_top(self):
        with test_database(test_db, (BaseModel, Lore)):
            add("bob", ["lore"])
            upvote([1])
            lores = get_top_lore(num=1)
            self.assertEqual(lores.get().author, "bob")

    def test_top_filtering_downvotes(self):
        with test_database(test_db, (BaseModel, Lore)):
            add("bob", ["lore"])
            add("alice", ["bad lore"])
            downvote([2])
            downvote([2])
            lores = get_top_lore(num=2)
            # Alice no longer has lore that shows up after filtering
            self.assertEqual(len(lores), 1)


class TestTags(TestCase):
    def test_tag(self):
        with test_database(test_db, (BaseModel, Lore, Tag, LoreTag)):
            tag = Tag.create(name="lasagna")
            lore = Lore.create(author="bob", lore="some lore")
            lore.tags.add(tag)
            self.assertEqual(lore.tags[0].name, "lasagna")

    def test_add_tag(self):
        with test_database(test_db, (BaseModel, Lore, Tag, LoreTag)):
            add("bob", ["lore"])
            add_tags(1, ["lasagna"])
            l = Lore.get(author="bob", lore="lore")
            self.assertIn("lasagna", [str(t) for t in l.tags])

    def test_remove_tag(self):
        with test_database(test_db, (BaseModel, Lore, Tag, LoreTag)):
            add("bob", ["lore"])
            add_tags(1, ["lasagna"])
            remove_tag(1, "lasagna")
            l = Lore.get(author="bob", lore="lore")
            self.assertNotIn("lasagna", [str(t) for t in l.tags])


if __name__ == '__main__':
    main()
