import random
import string
import sys
import unittest


major_version, _, _, _, _ = sys.version_info


if major_version == 3:
    from python3.dictionary import Dictionary
else:
    from python2.dictionary import Dictionary
    range = xrange



class Test(unittest.TestCase):

    def insert_random(self, n, low, high, thread_id=None):
        if thread_id:
            print('thread {} starting'.format(thread_id))
    
        for i in range(n):
            key = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                                for _ in range(random.randint(low, high)))
        
            value = random.randint(0, 1000)
            self.dictionary[key] = value
            self.reference[key] = value
    
        if thread_id:
            print('thread {} done'.format(thread_id))

    def test_single_thread_test_few_collisions(self):
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 1000)
        
        self.assertEqual(len(self.dictionary), len(self.reference))
        
        for key in self.reference:
            self.assertIn(key, self.dictionary)
            self.assertEqual(self.reference[key], self.dictionary[key])

    def test_single_thread_test_many_collisions(self):
        self.dictionary = Dictionary()
        self.reference = dict()
        self.insert_random(10000, 0, 2)
        
        self.assertEqual(len(self.dictionary), len(self.reference))
        
        for key in self.reference:
            self.assertIn(key, self.dictionary)
            self.assertEqual(self.reference[key], self.dictionary[key])
    
    def test_multi_thread_test_few_collisions(self):
        self.dictionary = Dictionary()
        self.reference = dict()
    
    def test_multi_thread_test_many_collisions(self):
        self.dictionary = Dictionary()
        self.reference = dict()



if __name__ == '__main__':
    unittest.main()
