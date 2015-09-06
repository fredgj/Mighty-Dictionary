import random
import string
import sys
import unittest
from threading import Thread

major_version, _, _, _, _ = sys.version_info


if major_version == 3:
    from python3.dictionary import Dictionary
else:
    from python2.dictionary import Dictionary
    range = xrange



class Test(unittest.TestCase):

    def assert_tests_passed(self):
        self.assertEqual(len(self.dictionary), len(self.reference))
        
        for key in self.reference:
            self.assertIn(key, self.dictionary)
            self.assertEqual(self.reference[key], self.dictionary[key])
    
    def insert_random(self, n, low, high, thread_id=None):
        if thread_id is not None:
            print('thread {} starting'.format(thread_id))
    
        for i in range(n):
            key = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                                for _ in range(random.randint(low, high)))
        
            value = random.randint(0, 1000)
            self.dictionary[key] = value
            self.reference[key] = value
    
        if thread_id is not None:
            print('thread {} done'.format(thread_id))

    def test_single_thread_test_few_collisions(self):
        print('\nRunning single threaded test with few collisions\n')
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 1000)
        
        self.assert_tests_passed()
        
        print('Single threaded test with few collisions passed')

    def test_single_thread_test_many_collisions(self):
        print('\nRunning single threaded test with many collisions\n')
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 2)
       
        self.assert_tests_passed()
        
        print('Single threaded test with many collisions passed')
    
    def test_multi_thread_test_few_collisions(self):
        print('\nRunning multi threaded test with few collisions\n')
        self.dictionary = Dictionary()
        self.reference = dict()

        threads = [Thread(target=self.insert_random, 
                          args=(1000, 0, 1000), 
                          kwargs={'thread_id': i})
                         for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()
        
        self.assert_tests_passed()

        print('Multi threaded test with few collisions passed')   
    
    def test_multi_thread_test_many_collisions(self):
        print('\nRunning multi threaded test with many collisions\n')
        self.dictionary = Dictionary()
        self.reference = dict()

        threads = [Thread(target=self.insert_random,
                          args=(10000, 0, 2),
                          kwargs={'thread_id': i})
                        for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        self.assert_tests_passed()

        print('Multi threaded test with many collisions passed')


if __name__ == '__main__':
    unittest.main()
