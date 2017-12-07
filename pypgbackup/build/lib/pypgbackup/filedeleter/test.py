import unittest
from subprocess import call
import removeoldbackups as rob
from os import path, utime
from freezegun import freeze_time
from datetime import timedelta, datetime


def touch(fname, times=None):
    times = (times.timestamp(), times.timestamp())
    with open(fname, 'a'):
        utime(fname, times)

@freeze_time("1990-12-31")
class TestFileRemoval(unittest.TestCase):
    test_folder = 'test_folder'
    
    def setUp(self):
        call(["mkdir", self.test_folder])
        self.month_start = path.join(self.test_folder, 'month_start.txt')
        self.month_end = path.join(self.test_folder, 'month_end.txt')
        self.older_10 = path.join(self.test_folder, 'older_10.txt')
        self.older_2 = path.join(self.test_folder, 'older_2.txt')
        self.february_28 = path.join(self.test_folder, 'february_28.txt')
        self.march_31 = path.join(self.test_folder, 'march_31.txt')
        
        now = datetime.now()
        touch(self.older_10,  now - timedelta(days=10))
        touch(self.older_2,  now - timedelta(days=2))
        touch(self.month_start, datetime(now.year, now.month, 1))
        touch(self.month_end, datetime(now.year, now.month, 31))
        touch(self.february_28, datetime(now.year, 2, 28))
        touch(self.march_31, datetime(now.year, 3, 31))
                
    def tearDown(self):
        call(["rm", "-rf", self.test_folder])

    def delete_files_older_than_week(self):
        rob.run("(now - mtime) > timedelta(days=7)", self.test_folder, False)
        self.assertEqual(path.isfile(self.month_start), False)
        self.assertEqual(path.isfile(self.month_end), True)
        self.assertEqual(path.isfile(self.older_10), False)
        self.assertEqual(path.isfile(self.older_2), True)
        self.assertEqual(path.isfile(self.february_28), False)
        self.assertEqual(path.isfile(self.march_31), False)
        
    def delete_files_not_start_end_of_month(self):
        rob.run("mtime.day != 1 and mtime.day != monthend", self.test_folder, False)
        self.assertEqual(path.isfile(self.month_start), True)
        self.assertEqual(path.isfile(self.month_end), True)
        self.assertEqual(path.isfile(self.older_10), False)
        self.assertEqual(path.isfile(self.older_2), False)
        self.assertEqual(path.isfile(self.february_28), True)
        self.assertEqual(path.isfile(self.march_31), True)

    def delete_files_not_start_end_of_month_or_older_than_week(self):
        rob.run("mtime.day != 1 and mtime.day != monthend and (now - mtime) > timedelta(days=7)", self.test_folder, False)
        self.assertEqual(path.isfile(self.month_start), True)
        self.assertEqual(path.isfile(self.month_end), True)
        self.assertEqual(path.isfile(self.older_10), False)
        self.assertEqual(path.isfile(self.older_2), True)
        self.assertEqual(path.isfile(self.february_28), True)
        self.assertEqual(path.isfile(self.march_31), True)
        

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestFileRemoval('delete_files_older_than_week'))
    suite.addTest(TestFileRemoval('delete_files_not_start_end_of_month'))
    suite.addTest(TestFileRemoval('delete_files_not_start_end_of_month_or_older_than_week'))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
