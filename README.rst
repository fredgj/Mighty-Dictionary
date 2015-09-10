Mighty Dictionary
=================

This is a reimplementation of pythons built-in dictionary, inspired by Brandon
Craig Rhodes talk `The Mighty Dictionary 
<https://www.youtube.com/watch?v=C4Kc8xzcA68>`_ from PyCon 2010.

There are two versions, a pyton 2 version and a python 3 version.
The python 2 version have been implemented to work exactly like pythons 2's
dictionary.

I wouldn't recommend using this dictionary, it's a lot slower than pythons
built-in dictionary (not that strange). It was implemented while exploring
the internal stucture of the dictionary and experimenting with pythons features.
I have made some minor changes from the python's dictionary implementation.

The strategy for calculating a new index in case of a collision has has been taken
from pythons `dictionary implementation
<https://hg.python.org/cpython/file/52f68c95e025/Objects/dictobject.c>`_ (line 35 to
125).

Differences
===========

It works like pythons dictionary, except for some extra syntactic sugar. 
If the keys are stored as strings, you can look them up like a attribute. If you have a
dictionary d = {'a': 1} you can use d.a to lookup 1.
This also works with adding new items to the dictionary or deleting items. 
d.b = 2 will add 2 to the dictionary with 'b' as its key, and del d.b will delete 
the entry. This is more or less useless unless you are
working in a python shell, where being able type d.a instead of
d['a'] the whole time might be handy, other than that it's nothing more than a 
neat functionality.

The python 2 version doesn't seem to shrink its entry table when deleting items
(leaving a dummy value in the entry table) and the entry table contains a number 
of entries that would fit in a smaller entry table. This is just a memory 
optimization, but shrinking the table, meaning inserting all the entries in a 
new table, takes time when there are many entries to be inserted.
Lets say the dictionary have been resized once meaning the size of the entry
table is 32 and all items except for one have been deleted, then the entry table would look like this:

.. code:: python

    [<entry>, dummy, dummy, dummy, dummy, dummy, None, ..., None]

Instread of keeping a huge table with lots of dummy values, this implementation
will shrink it when possible. So the table above would be shrinked to this:

.. code:: python
    
    [<entry>, None, None, None, None, None, None, None]

Bugs and issues
===============

There are probably a few bugs in the dictionary since it yet has to be testet
properly. 

Some of the code is a bit sketchy (global variables together setattr), and some
of it might be a bit overkill, but i wanted it to emulate pythons dictionary.

Resizing the table starts slowing down when the dictionary grows. This can't be
solved by threads due to pythons global interpreter lock (GIL) and the
dictionary's internal lock which would block the threads when inserting.
One way to solve this might be writing C extensions. 

The python 3 version doesn't seem to insert keys at the same index in the entry
table as the python 2 version when resizing.
There also seems to be some minor differences between pypy's and cpython's dict
implementations when inserting items. 
Therefore, when running the tests with python 3 or pypy the test won't check
if the two dictionaries are equal, just that they contain the same key, value
pairs.
