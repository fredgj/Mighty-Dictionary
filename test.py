import random
import string
import sys
import unittest
from threading import Thread, RLock


py_version = sys.version_info[0]


if py_version == 3:
    from python3.dictionary import Dictionary
else:
    from python2.dictionary import Dictionary
    range = xrange


class DictionaryTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DictionaryTest, self).__init__(*args, **kwargs)
        self.lock = RLock()

    def assert_tests_passed(self):
        self.assertEqual(len(self.dictionary), len(self.reference))
        if py_version == 3 or sys.executable.endswith('pypy'):
            for key in self.dictionary:
                self.assertIn(key, self.reference)
                self.assertEqual(self.dictionary[key], self.reference[key])
        else:
            self.assertEqual(self.dictionary, self.reference, msg='The two dictionaries are not equal')
            
            # only works if __delitem__ doesn't shrink the entry
            # table
            #while True:
            #    try:
            #        a = self.dictionary.popitem()
            #        b = self.reference.popitem()
            #        self.assertEqual(a,b)
            #    except KeyError:
            #        break
    
    def insert_random(self, n, low, high, thread_id=None):
        if thread_id is not None:
            print('Thread-{} starting'.format(thread_id))
        
        for i in range(n):
            key = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                                for _ in range(random.randint(low, high)))
        
            value = random.randint(0, 1000) 
            self.lock.acquire()
            self.dictionary[key] = value
            self.reference[key] = value
            self.lock.release()
    
        if thread_id is not None:
            print('Thread-{} done'.format(thread_id))

    def test_single_thread_test_many_unique_keys_(self):
        print('\nRunning single threaded test wit many unique keys\n')
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 1000)
        
        self.assert_tests_passed()
        
    def test_single_thread_test_few_unique_keys(self):
        print('\nRunning single threaded test with few unique keys\n')
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 1)
       
        self.assert_tests_passed()
        
    def test_multi_thread_test_many_unique_keys(self):
        print('\nRunning multi threaded test with many unique keys\n')
        self.dictionary = Dictionary()
        self.reference = dict()

        threads = [Thread(target=self.insert_random, 
                          args=(1000, 0, 1000), 
                          kwargs={'thread_id': i})
                         for i in range(1, 11)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()
        
        self.assert_tests_passed()

    def test_multi_thread_test_few_unique_keys(self):
        print('\nRunning multi threaded test with few unique keys\n')
        self.dictionary = Dictionary()
        self.reference = dict()

        threads = [Thread(target=self.insert_random,
                          args=(1000, 0, 1),
                          kwargs={'thread_id': i})
                        for i in range(1, 11)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        self.assert_tests_passed()


if __name__ == '__main__':
    unittest.main()
