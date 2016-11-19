from unittest import TestCase, main
from playhouse.test_utils import test_database
from peewee import SqliteDatabase
from datetime import datetime, timedelta

from loredb import BaseModel, Lore, compute_rating, vote

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


if __name__ == '__main__':
    main()
