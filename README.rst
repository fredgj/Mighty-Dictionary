Mighty Dictionary
=================

This is a reimplementation of pythons built-in dictionary, inspired by Brandon
Craig Rhodes talk The Mighty Dictionary from PyCon 2010.

It works like pythons dictionary in python 2. 

The strategy to calculate a new index in case of a collision has has been taken
from pythons `dictionary implementation
<https://hg.python.org/cpython/file/52f68c95e025/Objects/dictobject.c>`_ (line 35 to
125).

