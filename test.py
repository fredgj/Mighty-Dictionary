import random
import string
import sys
import unittest
from functools import wraps
from threading import Thread, RLock


py_version = sys.version_info[0]


if py_version == 3:
    from python3.dictionary import Dictionary
else:
    from python2.dictionary import Dictionary
    range = xrange


# Decorator for creating a thread, starting the thread, and being able to 
# retrieve the return value from the thread after it has terminated
# Return a function wrapped inside a thread.
def threaded(func):
    def wrapped_func(ret_val, *args, **kwargs):
        """Calls the function and appends the return value to ret_val"""
        val = func(*args, **kwargs)
        ret_val.append(val)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Creates a new thread with wrapped_func, adds an empty list to the
           thread for return value. Return a running thread"""
        ret_val = []
        thread = Thread(target=wrapped_func, args=(ret_val,)+args, kwargs=kwargs)
        thread.ret_val = ret_val
        thread.start()
        return thread

    return wrapper


class DictionaryTest(unittest.TestCase):
    def setUp(self):
        self.lock = RLock()

    def assert_insertion_tests_passed(self):
        self.assertEqual(len(self.dictionary), len(self.reference))
        if py_version == 3 or sys.executable.endswith('pypy'):
            for key in self.dictionary:
                self.assertIn(key, self.reference)
                self.assertEqual(self.dictionary[key], self.reference[key])
        else:
            self.assertEqual(self.dictionary, self.reference, 
                msg='The two dictionaries are not equal')
 
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

    def test_single_thread_insertion_test_many_unique_keys_(self):
        print('\nRunning single threaded insertion test with many unique keys\n')
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 1000)
        
        self.assert_insertion_tests_passed()
        
    def test_single_thread_insertion_test_few_unique_keys(self):
        print('\nRunning single threaded insertion test with few unique keys\n')
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 1)
       
        self.assert_insertion_tests_passed()
        
    def test_multi_thread_insertion_test_many_unique_keys(self):
        print('\nRunning multi threaded insertion test with many unique keys\n')
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
        
        self.assert_insertion_tests_passed()

    def test_multi_thread_insertion_test_few_unique_keys(self):
        print('\nRunning multi threaded insertion test with few unique keys\n')
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

        self.assert_insertion_tests_passed()

    @threaded
    def pop_all(self, n, default):
        for i in range(n):
            value = self.dictionary.pop(i, default)
            if value != i and value != default:
                return False, value, i
        return True, value, i

    @threaded
    def popitem_all(self):
        while True:
            try:
                self.dictionary.popitem()
            except KeyError as e:
                return str(e)

    @threaded
    def delete_all(self, n):
        """Delete is just here to compete 
           against either pop or popitem in
           removing items from the dictionary."""
        for i in range(n):
            try:
                del self.dictionary[i]
            except KeyError:
                continue
    
    def fill_dict_with_ints(self, n):
        for i in range(n):
            self.dictionary[i] = i

    def test_pop(self):
        print('\nRunning pop test\n')
        self.dictionary = Dictionary()
        n = 10000
        default = 2
        self.fill_dict_with_ints(n)
        
        t1 = self.pop_all(n, default)
        t2 = self.delete_all(n)

        t1.join()
        t2.join()
        
        ret_val, value, expected = t1.ret_val[0]
        
        self.assertTrue(ret_val, 
            msg="pop returned {}, expected to return {} or {}".format(value,
                                                                      expected,
                                                                      default,))

    def test_popitem(self):
        print('\nRunning popitem test\n')
        self.dictionary = Dictionary()
        n = 10000
        self.fill_dict_with_ints(n)

        t1 = self.popitem_all()
        t2 = self.delete_all(n)

        t1.join()
        t2.join()
        
        msg = "'popitem(): dictionary is empty'"
        excpt_msg = t1.ret_val[0]
        
        self.assertEqual(excpt_msg, msg, 
            msg="Popitem returned '{}', should return '{}'".format(excpt_msg, 
                                                                   msg)) 


if __name__ == '__main__':
    unittest.main()
