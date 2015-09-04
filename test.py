import random
import string
from dictionary import Dictionary


#d = Dictionary()

#for i in xrange(100000):
#    key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(1,20)))
#    value = random.randint(0,100)
#    d[key] = value
#    print '{}: inserting: <{}, {}>'.format(i, key, value)


d = Dictionary()
s = set()
n = 10000
print 'generating {} random keys'.format(n)


for i in xrange(n):
    key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(1,20)))
    s.add((key, 1))


print 'inserting keys to dictionary'


for key, value in s:
    d[key] = value


print 'done inserting'


print 'dictionary length: {}, set length: {}'.format(len(d), len(s))
assert len(d) == len(s)


print 'cecking keys'
for key, _ in s:
    assert key in d


print 'all keys found in dictionary'
print 'everything went well'

