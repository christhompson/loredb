from unittest import TestCase, main
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
from datetime import datetime, timedelta

from loredb import BaseModel, Lore, compute_rating, vote, add, get_top_lore

test_db = SqliteDatabase(':memory:')
test_time = datetime.now()


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

    def create_test_data(self):
        # Create some lore
        for i in range(10):
            t = test_time + timedelta(i*100)
            lore = "lore #%d" % i
            Lore.create(time=t, author=str(i), lore=lore)

    def test_initial_rating(self):
        # Setup
        with test_database(test_db, (BaseModel, Lore)):
            self.create_test_data()
            self.assertEqual(Lore.get(time=test_time).lore, "lore #0")
            self.assertEqual(Lore.get(time=test_time).rating, 4 / 14)

    def test_upvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            self.create_test_data()
            vote(1, which='up')
            self.assertEqual(Lore.get(time=test_time).upvotes, 5)
            self.assertEqual(Lore.get(time=test_time).rating, 5 / 15)

    def test_downvote(self):
        with test_database(test_db, (BaseModel, Lore)):
            self.create_test_data()
            vote(1, which='down')
            self.assertEqual(Lore.get(time=test_time).downvotes, 11)
            self.assertEqual(Lore.get(time=test_time).rating, 4 / 15)


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
    def create_test_data(self):
        # Create some lore
        for i in range(10):
            t = test_time + timedelta(i*100)
            lore = "lore #%d" % i
            Lore.create(time=t, author=str(i), lore=lore)

    def test_top(self):
        with test_database(test_db, (BaseModel, Lore)):
            add("bob", ["lore"])
            vote(1, which="up")
            lores = get_top_lore(num=1)
            self.assertEqual(lores.get().author, "bob")

    def test_top_filtering_downvotes(self):
        with test_database(test_db, (BaseModel, Lore)):
            add("bob", ["lore"])
            add("alice", ["bad lore"])
            vote(2, which="down")
            vote(2, which="down")
            lores = get_top_lore(num=2)
            # Alice no longer has lore that shows up after filtering
            self.assertEqual(len(lores), 1)


if __name__ == '__main__':
    main()
