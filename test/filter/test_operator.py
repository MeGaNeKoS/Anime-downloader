import unittest

from src.filter.operator import Operator


class OperatorTest(unittest.TestCase):
    def test_contains(self):
        # Test the "contains" operator
        func = Operator.get_function("contains")
        self.assertTrue(func("Hello, world!", "Hello"))
        self.assertFalse(func("Hello, world!", "foo"))

    def test_begin_with(self):
        # Test the "begin_with" operator
        func = Operator.get_function("begin_with")
        self.assertTrue(func("Hello, world!", "Hello"))
        self.assertFalse(func("Hello, world!", "world"))

    def test_greater_than(self):
        # Test the "greater_than" operator
        func = Operator.get_function("greater_than")
        self.assertTrue(func(10, 5))
        self.assertFalse(func(5, 10))

    def test_greater_than_or_equal(self):
        # Test the "greater_than_or_equal" operator
        func = Operator.get_function("greater_than_or_equal")
        self.assertTrue(func(10, 5))
        self.assertTrue(func(5, 5))
        self.assertFalse(func(5, 10))

    def test_less_than(self):
        # Test the "less_than" operator
        func = Operator.get_function("less_than")
        self.assertTrue(func(5, 10))
        self.assertFalse(func(10, 5))
        self.assertFalse(func(5, 5))

    def test_less_than_or_equal(self):
        # Test the "less_than_or_equal" operator
        func = Operator.get_function("less_than_or_equal")
        self.assertTrue(func(5, 10))
        self.assertTrue(func(5, 5))
        self.assertFalse(func(10, 5))

    def test_in(self):
        # Test the "in" operator
        func = Operator.get_function("in")
        self.assertTrue(func(5, (1, 2, 3, 4, 5)))
        self.assertFalse(func(10, (1, 2, 3, 4, 5)))

    def test_equal(self):
        # Test the "equal" operator
        func = Operator.get_function("equal")
        self.assertTrue(func(5, 5))
        self.assertFalse(func(5, 10))

    def test_default(self):
        # Test the default operator
        func = Operator.get_function("foo")
        self.assertTrue(func("foo", "bar"))

