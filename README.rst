Mighty Dictionary
=================

This is a reimplementation of pythons built-in dictionary, inspired by Brandon
Craig Rhodes talk `The Mighty Dictionary 
<https://www.youtube.com/watch?v=C4Kc8xzcA68>`_ from PyCon 2010.

This dictionary was implemented while exploring the internal stucture of the 
dictionary and experimenting with pythons features. I have made some minor 
changes from the python's dictionary implementation, but they work more or less
the same way.

This dictionary implenentation as a lot slower compared to pythons built-in
dictionary, but it's mainly because this dictionary is implemented in python
while pythons dictionary is implemented in C.

There are two versions, a pyton 2 version and a python 3 version.
The python 2 version have been implemented to work exactly like pythons 2's
dictionary.

The strategy for calculating a new index in case of a collision has has been taken
from pythons `dictionary implementation
<https://hg.python.org/cpython/file/52f68c95e025/Objects/dictobject.c>`_ (line 35 to
125 and line 318 to 395).

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


Bugs and issues
===============

There are probably a few bugs in the dictionary since it yet has to be testet
properly. 

The dictionary should be thread-safe. All the critical zones are protected by
a reentrant lock, though this has yet to be fully tested.

Some of the code is a bit sketchy (global variables together setattr), and some
of it might be a bit overkill, but i wanted it to emulate pythons dictionary.

The python 3 version doesn't seem to insert keys at the same index in the entry
table as the python 2 version when resizing.
There also seems to be some minor differences between pypy's and cpython's dict
implementation's algorithm for calculating indexes in the entry table. 
Therefore, when running the tests with python 3 or pypy the test won't check
if the two dictionaries are equal, just that they contain the same key, value
pairs.
