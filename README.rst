Mighty Dictionary
=================

This is a reimplementation of pythons built-in dictionary, inspired by Brandon
Craig Rhodes talk `The Mighty Dictionary 
<https://www.youtube.com/watch?v=C4Kc8xzcA68>`_ from PyCon 2010.

I wouldn't recommend using this dictionary, it's a lot slower than pythons
built-in dictionary (not that strange). It was implemented while exploring
the internal stucture of the dictionary and experimenting with pythons features.

It works like pythons dictionary in python 2, except for some extra syntactic sugar. 
If the keys are stored as strings, you can look them up like a attribute. If you have a
dictionary d = {'a': 1} you can use d.a to lookup 1.
This also works with adding new items to the dictionary or deleting items. 
d.b = 2 will add 2 to the dictionary with 'b' as its key, and del d.b will delete 
the entry. This is more or less useless unless you are
working in a python shell, where being able type d.a instead of
d['a'] the whole time might be handy, other than that it's nothing more than a 
neat functionality.

The strategy for calculating a new index in case of a collision has has been taken
from pythons `dictionary implementation
<https://hg.python.org/cpython/file/52f68c95e025/Objects/dictobject.c>`_ (line 35 to
125).


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

