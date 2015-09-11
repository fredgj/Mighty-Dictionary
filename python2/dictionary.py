# This is a reimplementation of pythons built-in dictionary
# inspired by Brandon Craig Rhodes talk from PyCon 2010: The Mighty Dictionary


from threading import RLock
from ctypes import c_size_t
from itertools import izip


# Meta class to control what class name type returns
class TypeReturn(type):
    def __repr__(cls):
        name = cls.__name__
        name = name[1:] if name.startswith('_') else name
        return "<type '{}'>".format(name)


# Dummy class for leaving a dummy value until next
# time the dictionary gets resized in case a key already has collided with
# the index where the deleted object was stored
class _Dummy(object):
    __metaclass__ = TypeReturn

    def __repr__(self):
        return 'Dummy'


class __sequence_iterator(object):
    """Used by iteritems, iterkeys and itervalues to create an
       iterator over dictionary items, keys or values"""
    
    __metaclass__ = TypeReturn
    
    def __init__(self, sequence_gen, dictionary):
        global _iter_counter, _iter_local_vars
        _iter_counter = 0
        _iter_local_vars = 3
        self.__sequence = sequence_gen
        self.__dictionary = dictionary
        self.__size = len(dictionary)
        # Hide the underscore from class name whenever printing it
        name = self.__class__.__name__
        self.__class__.__name__ = name[1:] if name.startswith('_') else name

    def __iter__(self):
        return self

    def next(self):
        if len(self.__dictionary) != self.__size:
            raise RuntimeError('dictionary changed size during iteration')
        else:
            return(next(self.__sequence))

    def __repr__(self):
        cls = self.__class__.__name__
        address = hex(id(self))
        return '<{} object at {}>'.format(cls, address)
    
    # prevents a user to add more attributes 
    # or reasign instance attributes.
    def __setattr__(self, name, value):
        global _iter_counter, _iter_local_vars
        
        if _iter_counter < _iter_local_vars:
            self.__dict__[name] = value
            _iter_counter += 1
        else:
            cls = self.__class__.__name__
            raise AttributeError("{} object has not attribute {}".format(cls, name))


class _dictionary_keyiterator(__sequence_iterator):
    pass


class _dictionary_valueiterator(__sequence_iterator):
    pass


class _dictionary_itemiterator(__sequence_iterator):
    pass


class __dictionary_view(object):
    """provide a dynamic view on the dictionary's entries, which means that 
       when the dictionary changes, the view reflects this canges."""
    
    __metaclass__ = TypeReturn

    def __init__(self, dictionary):
        global _view_counter, _view_local_vars
        _view_counter = 0
        _view_local_vars = 1
        self._dictionary = dictionary
        name = self.__class__.__name__
        self.__class__.__name__ = name[1:] if name.startswith('_') else name

    def __len__(self):
        return len(self._dictionary)

    def __and__(self, other):
        self_items = [item for item in self if item in other]
        other_items = [item for item in other if item in self]
        return set(self_items + other_items)

    def __rand__(self, other):
        return self & other

    def __or__(self, other):
        self_items = [item for item in self]
        other_items = [item for item in other]
        return set(self_items + other_items)

    def __ror__(self, other):
        return self | other

    def __sub__(self, other):
        return {item for item in self if item not in other}

    def __rsub__(self, other):
        return {item for item in other if item not in self}

    def __xor__(self, other):
        self_items = [item for item in self if item not in other]
        other_items = [item for item in other if item not in self]
        return set(self_items + other_items)

    def __rxor__(self, other):
        return self ^ other

    def __setattr__(self, name, value):
        global _view_counter, _view_local_vars
        
        if _view_counter < _view_local_vars:
            self.__dict__[name] = value
            _view_counter += 1
        else:
            cls = self.__class__.__name__
            raise AttributeError("{} object has not attribute {}".format(cls, name))

class _dictionary_keys(__dictionary_view):
    def __iter__(self):
        for key in self._dictionary.iterkeys():
            yield key

    def __repr__(self):
        cls = self.__class__.__name__
        keys = ''
        for key in self:
            if type(key) is str:
                key = "'" + key + "'"
            keys += '%s, ' % key
        return '{}([{}])'.format(cls, keys[:-2])


class _dictionary_values(__dictionary_view):
    def __iter__(self):
        for value in self._dictionary.itervalues():
            yield value

    def __repr__(self):
        cls = self.__class__.__name__
        values = ''
        for value in self:
            if type(value) is str:
                value = "'" + value + "'"
            values += '%s, ' % value
        return '{}([{}])'.format(cls, values[:-2])
        

class _dictionary_items(__dictionary_view):
    def __iter__(self):
        for key, value in self._dictionary.iteritems():
            yield key, value
            
    def __repr__(self):
        cls = self.__class__.__name__
        items = ''
        for key, value in self:
            if type(key) is str:
                key = "'" + key + "'"
            if type(value) is str:
                value = "'" + value + "'"
            items += '(%s, %s), ' % (key, value)
        return '{}([{}])'.format(cls, items[:-2])


class Dictionary(object):
    
    __BASE_SIZE = 8
    
    # Sequence must be either another dictionary or
    # a sequece of key-value pairs so self[key] = value
    def __init__(self, sequence=None, **kwargs):
        self.clear()
        if sequence or kwargs:
            self.update(sequence, **kwargs)
    
    @property
    def debug(self):
        return self.__entries

    @classmethod
    def fromkeys(cls, seq, value=None):
        """Create a new dictionary with keys from seq and 
           values set to value"""
        new_dict = cls()
        for key in seq:
            new_dict[key] = value
        return new_dict
    
    def __len__(self):
        """Return the number of items in the dictionary."""
        return self.__len
    

    def __contains__(self, key):
        """Return true if dictionary has key else false."""
        index = self.__get_index(key)
        return self.__entries[index] is not None
         
    # The default argument 'shrink' is used internally to prevent recursive 
    # shrinking when inserting entries into the entry table after 
    # resizing/shrinking the entry table
    def __setitem__(self, key, value, shrink=True):
        """Set dictionary[key] to value."""
        self.lock.acquire()
        index = self.__get_index(key)
        entry = self.__entries[index]

        if entry is None:
            self.__len += 1    
            self.__true_len += 1
        elif type(entry) is _Dummy:
            self.__len += 1
        
        self.__entries[index] = (hash(key), key, value) 
        
        if self.__true_len >= (len(self.__entries) * (2.0/3.0)):
            self.__resize()    
        elif shrink:
            if len(self) < self.__prev_size * (2.0/3.0) and self.__size > self.__BASE_SIZE:
                self.__shrink()
        
        self.lock.release()
    
    def __getitem__(self, key):
        """Return the item of dictionary with key 'key'.
           Raises a KeyError if key is not in the map."""
        self.lock.acquire()
        index = self.__get_index(key)
        entry = self.__entries[index]
        
        if entry and type(entry) is not _Dummy:
            _, _, value = entry
            self.lock.release()
            return value
        else:
            self.lock.release()
            raise KeyError(key)

    # The default argument 'index' is used internally when the index
    # already has been calculated
    def __delitem__(self, key, index=None):
        """Remove dictionary[key] from dictionary.
           Raises a KeyError if key is not in the map"""
        self.lock.acquire()
        index = index if index is not None else self.__get_index(key)
        
        if self.__entries[index]:
            self.__len -= 1
            self.__entries[index] = _Dummy()
        else:
            self.lock.release()
            raise KeyError(key)
        
        self.lock.release()

    # dictionary.key, same as dictionary[key]
    # return __getitem__(key)
    def __getattr__(self, key):
        return self[key]
    
    # checks if all instance variables have been initialized,
    # inserts them into the instance dictionry if not, or if
    # changing the value of an instance variable
    # else call __setitem__
    # dictionary.key = value, same as dictonary[key] = value
    def __setattr__(self, name, value):
        global _dict_counter, _dict_local_vars
        
        if name in self.__dict__:
            self.__dict__[name] = value
        elif _dict_counter < _dict_local_vars:
            self.__dict__[name] = value
            _dict_counter += 1
        else:
            self[name] = value
    
    # del dictionary.key, same as del dictionary[key]
    def __delattr__(self, key):
        del self[key] 
    
    def __iter__(self):
        """Return an iterator over the keys in the dictionary.
           This it a shortcut for iterkeys()."""
        return self.iterkeys()
    
    # Not a proper repr, but returns a string so it looks like 
    # pythons built-in dictionary
    def __repr__(self):
        items = ''
        for _, key, value in self.__get_entries():
            if type(key) is str:
                key = "'" + key + "'"
            if type(value) is str:
                value = "'" + value + "'"
            items += str(key) + ': ' + str(value) + ', '

        return '{' +  items[:-2] + '}'

    def __eq__(self, other):
        type_other = type(other)
        if type_other is Dictionary or type_other is dict:
            dicts = izip(self, other)
            return all(key1==key2 and self[key1]==other[key2] 
                       for key1, key2 in dicts)
        else:
            return False
    
    def __hash__(self):
        cls = self.__class__.__name__
        raise TypeError("unhashable type: '{}'".format(cls))

    def clear(self):
        """Remove all items from the dictionary"""
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        _dict_local_vars = 6
        self.lock = RLock()
        self.__len = 0
        self.__true_len = 0
        self.__size = self.__BASE_SIZE
        self.__prev_size = self.__size
        self.__entries = [None] * self.__size

    def copy(self):
        """Return a shallow copy of the dictionary"""
        return self.__class__(self.iteritems())

    def get(self, key, default=None):
        """Return the value for key if key is in the dictionary, else default.
           If default is not given, it defaults to None, so that this method 
           never raises a keyerror."""
        try:    
            return self[key]
        except KeyError:
            return default

    def has_key(self, key):
        """Test for the presence of key in dictionary."""
        return key in self
     
    def pop(self, key, default=None):
        """If the key is in the dictionary, remove it and return its value, 
           else return default. If default is not given, and key is not in the
           dictionary, a KeyError is raised."""
        index = self.__get_index(key)
        entry = self.__entries[index]
        
        if entry and type(entry) is not _Dummy:
            _,_, value = item
            self.__delitem__(key, index=index)
            return value
        elif default:
            return default
        else:
            raise KeyError(key)

    def popitem(self):
        """Remove and return and remove an arbitrary (key, value) pair from the
           dictionary"""
        try:
            key, value = next(self.iteritems())
            index = self.__get_index(key)
            entry = self.__entries[index]
            if entry is not None:
                self.__delitem__(key, index=index)
                return key,value
        except StopIteration:
            raise KeyError('popitem(): dictionary is empty')   
    
    def setdefault(self, key, default=None):
        """If the key is in the dictionary, return its value. If not, insert key
           with a value of default and return default. Default defaults to None."""
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def update(self, other=None, **kwargs):
        """Update the dictionary with the key/value pairs from other, 
           overwriting existing keys. Return None"""
        if other:
            if hasattr(other, 'keys'):
                self.__insert_from_dict(other)
            else:
                self.__insert_from_sequence(other)
        self.__insert_from_dict(kwargs)
    
    def keys(self):
        """Return a copy of the dictionary's keys"""
        return [key for _, key, _ in self.__get_entries()]

    def items(self):
        """Return a copy of the dictionary's list of (key, value) pairs."""
        return [(key, value) for _, key, value in self.__get_entries()]

    def values(self):
        """Return a copy of the dictionary's list of values"""
        return [value for _, _, value in self.__get_entries()]

    def iterkeys(self):
        """Return an iterator over the dictionary's keys"""
        keys = (key for _, key, _ in self.__get_entries())
        return _dictionary_keyiterator(keys, self)

    def iteritems(self):
        """Return an iterator over the dictionary's (key, value) pairs"""
        items = ((key, value) for _, key, value in self.__get_entries())
        return _dictionary_itemiterator(items, self)

    def itervalues(self):
        """Return an iterator over the dictionary's values"""
        values = (value for _, _, value in self.__get_entries())
        return _dictionary_valueiterator(values, self)

    def viewkeys(self):
        """Return a new view of the dictionary's keys"""
        return _dictionary_keys(self)

    def viewvalues(self):
        """Return a new view of the dictionary's values"""
        return _dictionary_values(self)

    def viewitems(self):
        """Return a new view of the dictionary's items (key/value pairs)."""
        return _dictionary_items(self)

    def __insert_from_dict(self, other):
        for key in other:
            self[key] = other[key]

    # Inserts key/value pairs from a sequence, 
    # raises a ValueError if ValueError if not key/value pair
    def __insert_from_sequence(self, sequence):
        for i, pair in enumerate(sequence):
            length = len(pair)
            
            if length != 2:
                raise ValueError('dictionary update sequence element #{} has lenght {}; 2 is required'.format(i, length))
            
            key, value = pair
            self[key] = value
    
    # Returing a generator expression is the only thing that works here because 
    # later we will need it in __resize -> __add_entries where all entries from 
    # the entry table (__entries) are deleted before inserting them to the new 
    # table. Defining generator object with yield wouldn't work since the 
    # entries would already be deleted when generating the entries.
    def __get_entries(self):
        return (entry for entry in self.__entries if entry and type(entry) is not _Dummy)
    
    # A general-purpose method that returns an index where 
    # either key is found or can be inserted.
    def __get_index(self, key):
        mask = self.__size-1
        key_hash = c_size_t(hash(key))
        index = key_hash.value & mask
        freeslot = None
        
        if self.__valid_index(index, key):
            return index
        elif type(self.__entries[index]) is _Dummy:
            freeslot = index
            
        # A collision occured. Tries the other bits of the hash
        i = index
        perturb = key_hash

        while True:
            i = (i << 2) + i + perturb.value + 1
            index = i & mask
            
            if self.__entries[index] is None:
                return index if freeslot is None else freeslot
            elif self.__valid_index(index, key):
                return index
            elif type(self.__entries[index]) is _Dummy and freeslot is None:
                    freeslot = index
            
            perturb.value >>= 5
    
    # Return True if index in entry table is empty or the entry has the same 
    # hash and key as key and its hash value.
    def __valid_index(self, index, key):
        entry = self.__entries[index]
        if entry is None:
            return True
        elif type(entry) is not _Dummy:
            entry_hash, entry_key, _ = entry
            return entry_hash == hash(key) and entry_key == key
    
    # Resize it if its more than 2/3 full, else just delete dummy values 
    # from the table and insert the entris into the fresh table
    def __resize(self):
        # Checks if dictionary really need to resize
        # or just have to get rid of Dummy entries
        if len(self) >= (len(self.__entries) * (2.0/3.0)):
            if self.__true_len < 50000:
                self.__size *= 4
                prev = self.__prev_size/4
                self.__prev_size = prev if prev > self.__BASE_SIZE else self.__BASE_SIZE
            else:
                self.__size *= 2
                self.__prev_size /= 2
        
        self.__len = 0
        self.__true_len = 0
        self.__add_entries()
        
    # The opposite as resize, this method shrinks the entry table.
    # This happens when there are dummy values stored in the entry table
    # and the number of items could fit in a smaller entry table
    def __shrink(self):
        self.__size /= 4 if len(self) < 50000 else 2
        #self.__prev_size
        self.__len = 0
        self.__true_len = 0
        self.__add_entries()
    
    # Helper function used by resize and shink to reset the entry 
    # table and insert all items into the new entry table
    def __add_entries(self):
        entries = self.__get_entries()
        self.__entries = [None] * self.__size

        for _, key, value in entries:
            self.__setitem__(key, value, shrink=False)
    
