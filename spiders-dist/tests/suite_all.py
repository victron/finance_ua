import unittest


loader = unittest.TestLoader()
suite_all = loader.discover('.')
# print(suite_all)

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite_all)

# unittest.TextTestRunner().run(suite_all)

# if __name__ is '__main__':


