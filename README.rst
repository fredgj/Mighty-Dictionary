Mighty Dictionary
=================

This is a reimplementation of pythons built-in dictionary, inspired by Brandon
Craig Rhodes talk `The Mighty Dictionary 
<https://www.youtube.com/watch?v=C4Kc8xzcA68>`_ from PyCon 2010.

It works like pythons dictionary in python 2, except for some extra syntactic sugar. 
If the keys are stored as strings, you can look them up like a attribute. If you have a
dictionary d = {'a':1} you can use d.a to lookup 1.
This also works with adding new items to the dictionary. d.b = 2 will add 2 to
the dictionary with 'b' as its key. This is completely useless unless you are
working in a python shell, where it might come in handy to type d.a instead of
d['a'] the whole time, other than that it's useless (but cool).

The strategy to calculate a new index in case of a collision has has been taken
from pythons `dictionary implementation
<https://hg.python.org/cpython/file/52f68c95e025/Objects/dictobject.c>`_ (line 35 to
125).

