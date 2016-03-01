import unittest

class BasicTests(unittest.TestCase):

  def test_one(self):
      self.assertEqual('foo'.upper(), 'FOO')

  def test_two(self):
      self.assertTrue('FOO'.isupper())
      self.assertFalse('Foo'.isupper())

if __name__ == '__main__':
    unittest.main()