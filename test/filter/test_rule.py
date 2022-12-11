import unittest

from src.filter.rule import RuleCollection, RuleManager


class RuleCollectionTest(unittest.TestCase):
    def setUp(self):
        # Create a new Rules instance to use in the test
        self.rules = RuleCollection()

    def test_add(self):
        # Test the add method
        self.rules.add("file_name", "contains", "foo")
        self.rules.add("file_name", "greater_than", 5)
        self.rules.add("file_name", "in", (1, 2, 3, 4, 5))

        self.assertEqual(self.rules.rules,
                         [("file_name", "contains", "foo", False, True),
                          ("file_name", "greater_than", 5, False, True),
                          ("file_name", "in", (1, 2, 3, 4, 5), False, True)])

    def test_remove(self):
        # Test the remove method
        self.rules.add("file_name", "contains", "foo")
        self.rules.add("file_name", "greater_than", 5)
        self.rules.add("file_name", "in", (1, 2, 3, 4, 5))

        self.rules.remove("file_name", "contains", "foo")
        self.rules.remove("file_name", "greater_than", 5)
        self.rules.remove("file_name", "in", (1, 2, 3, 4, 5))

        self.assertEqual(self.rules.rules, [])

    def test_match_all(self):
        self.rules.add("file_name", "contains", "foobar")
        self.rules.add("file_name", "contains", "baz")

        self.assertTrue(self.rules.check({"file_name": "foobarbaz"}))
        self.assertFalse(self.rules.check({"file_name": "foobar"}))
        self.assertFalse(self.rules.check({"file_name": "baz"}))

    def test_match_any(self):
        self.rules.match_all = False
        self.rules.add("file_name", "contains", "foobar")
        self.rules.add("file_name", "contains", "baz")

        self.assertTrue(self.rules.check({"file_name": "foobarbaz"}))
        self.assertTrue(self.rules.check({"file_name": "foobar"}))
        self.assertTrue(self.rules.check({"file_name": "baz"}))

    def test_match_all_negate(self):
        self.rules.add("file_name", "contains", "foobar", negate=True)
        self.rules.add("file_name", "contains", "baz", negate=True)

        self.assertFalse(self.rules.check({"file_name": "foobarbaz"}))
        self.assertFalse(self.rules.check({"file_name": "foobar"}))
        self.assertFalse(self.rules.check({"file_name": "baz"}))

    def test_match_any_negate(self):
        self.rules.match_all = False
        self.rules.add("file_name", "contains", "foobar", negate=True)
        self.rules.add("file_name", "contains", "baz", negate=True)

        self.assertFalse(self.rules.check({"file_name": "foobarbaz"}))
        self.assertTrue(self.rules.check({"file_name": "foobar"}))
        self.assertTrue(self.rules.check({"file_name": "baz"}))

    def test_match_all_inactive(self):
        self.rules.add("file_name", "contains", "foobar", active=False)
        self.rules.add("file_name", "contains", "baz", active=False)

        self.assertTrue(self.rules.check({"file_name": "foobarbaz"}))
        self.assertTrue(self.rules.check({"file_name": "foobar"}))
        self.assertTrue(self.rules.check({"file_name": "baz"}))

    def test_match_any_inactive(self):
        self.rules.match_all = False
        self.rules.add("file_name", "contains", "foobar", active=False)
        self.rules.add("file_name", "contains", "baz", active=False)

        self.assertTrue(self.rules.check({"file_name": "foobarbaz"}))
        self.assertTrue(self.rules.check({"file_name": "foobar"}))
        self.assertTrue(self.rules.check({"file_name": "baz"}))

    def test_inactive_collection(self):
        self.rules.active = False
        self.rules.add("file_name", "contains", "foobar")
        self.rules.add("file_name", "contains", "baz")

        self.assertTrue(self.rules.check({"file_name": "foobarbaz"}))
        self.assertTrue(self.rules.check({"file_name": "foobar"}))
        self.assertTrue(self.rules.check({"file_name": "baz"}))


class RuleManagerTest(unittest.TestCase):
    def setUp(self):
        # Create a new RuleManager instance to use in the test
        self.manager = RuleManager()

    def test_add_collection(self):
        # Test the add_collection method
        collection1 = RuleCollection()
        collection2 = RuleCollection()

        self.manager.add_collection("my_test 1", collection1)
        self.manager.add_collection("my_test 2", collection2)

        self.assertEqual({
            'my_test 1': collection1,
            'my_test 2': collection2
        },
            self.manager.collections)

    def test_remove_collection(self):
        # Test the remove_collection method
        collection1 = RuleCollection()
        collection2 = RuleCollection()

        self.manager.add_collection("my_test 1", collection1)
        self.manager.add_collection("my_test 2", collection2)

        self.manager.remove_collection("my_test 1")

        self.assertEqual({"my_test 2": collection2}, self.manager.collections)

    def test_remove_collection_fail(self):
        # Test the remove_collection method
        collection1 = RuleCollection()
        collection2 = RuleCollection()

        self.manager.add_collection("my_test 1", collection1)
        self.manager.add_collection("my_test 2", collection2)

        self.manager.remove_collection("my_test 1")
        self.manager.remove_collection("my_test 1")

        self.assertEqual({"my_test 2": collection2}, self.manager.collections)

    def test_check(self):
        # Test the check method
        collection1 = RuleCollection()
        collection1.add("file_name", "contains", "foobar")
        collection1.add("file_name", "contains", "baz")

        collection2 = RuleCollection()
        collection2.match_all = False
        collection2.add("file_name", "contains", "foobar")
        collection2.add("file_name", "contains", "baz")

        self.manager.add_collection("my_test 1", collection1)
        self.manager.add_collection("my_test 2", collection2)

        # The check method should return True because both collections match
        self.assertTrue(self.manager.check({"file_name": "foobarbaz"}))

        # The check method should return False because one of the collections does not match
        self.assertFalse(self.manager.check({"file_name": "foobar"}))
        self.assertFalse(self.manager.check({"file_name": "baz"}))

        # Test with inactive collections
        collection1.active = False
        collection2.active = False

        # The check method should return True because both collections are inactive
        self.assertTrue(self.manager.check("foobarbaz"))

    def test_serialize(self):
        # Test the serialize method
        collection1 = RuleCollection()
        collection1.add("file_name", "contains", "foobar")
        collection1.add("file_name", "contains", "baz")

        collection2 = RuleCollection()
        collection2.match_all = False
        collection2.add("file_name", "contains", "foobar")
        collection2.add("file_name", "contains", "baz")

        self.manager.add_collection("my_test 1", collection1)
        self.manager.add_collection("my_test 2", collection2)
        self.assertEqual({
            "Rules": {
                "my_test 1": {
                    "match_all": True,
                    "active": True,
                    "rules": [
                        (
                            "file_name",
                            "contains",
                            "foobar",
                            False,
                            True
                        ),
                        (
                            "file_name",
                            "contains",
                            "baz",
                            False,
                            True
                        )
                    ]
                },
                "my_test 2": {
                    "match_all": False,
                    "active": True,
                    "rules": [
                        (
                            "file_name",
                            "contains",
                            "foobar",
                            False,
                            True
                        ),
                        (
                            "file_name",
                            "contains",
                            "baz",
                            False,
                            True
                        )
                    ]
                }
            }
        },
            self.manager.__dict__())
