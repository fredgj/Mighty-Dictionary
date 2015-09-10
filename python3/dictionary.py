# This is a reimplementation of pythons built-in dictionary
# inspired by Brandon Craig Rhodes talk from PyCon 2010: The Mighty Dictionary

from threading import RLock
from ctypes import c_size_t


# Meta class to control what class name type returns
class TypeReturn(type):
    def __repr__(cls):
        name = cls.__name__
        name = name[1:] if name.startswith('_') else name
        return "<type '{}'>".format(name)


# Dummy class for leaving a dummy value until next
# time the dictionary gets resized in case a key already has collided with
# the index where the deleted object was stored
class _Dummy(metaclass=TypeReturn):
    def __repr__(self):
        return 'Dummy'


class __dictionary_view(metaclass=TypeReturn):
    def __init__(self, dictionary):
        global _view_counter, _view_local_vars
        _view_counter = 0
        _view_local_vars = 2
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
        _view_counter += 1
        if _view_counter < _view_local_vars:
            self.__dict__[name] = value
        elif hasattr(self, name):
            self.__dict__[name] = value
        else:
            cls = self.__class__.__name__
            raise AttributeError("{} object has not attribute {}".format(cls, name))


class _dictionary_keys(__dictionary_view):
    def __iter__(self):
        yield from self._dictionary

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
        for key in self._dictionary:
            yield self._dictionary[key]

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
        for key in self._dictionary:
            yield key, self._dictionary[key]
            
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


class Dictionary:
    
    __BASE_SIZE = 8
    
    # Sequence must be either anther dictionary or
    # a sequece of key-value pairs so self[key] = value
    def __init__(self, sequence=None, **kwargs):
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        _dict_local_vars = 5
        self.lock = RLock()
        self.__size = self.__BASE_SIZE
        self.__prev_size = self.__size
        self.__n = 3
        self.__entries = [None] * self.__size
        if sequence or kwargs:
            self.update(sequence, **kwargs)
    
    @property
    def debug(self):
        return self.__entries

    @classmethod
    def fromkeys(cls, seq, value=None):
        new_dict = cls()
        for key in seq:
            new_dict[key] = value
        return new_dict
    
    def __len__(self):
        return len([entry for entry in self.__get_entries()])
    
    # also count Dummy entries
    def __true_len(self):
        return len([entry for entry in self.__entries if entry])

    def __contains__(self, key):
        index = self.__get_index(key)
        return self.__entries[index] is not None
         
    def __setitem__(self, key, value, index=None):
        self.lock.acquire()
        index = index if index is not None else self.__get_index(key)
        self.__entries[index] = (hash(key), key, value) 

        size = self.__true_len()
        if size >= (len(self.__entries) * (2.0/3.0)):
            self.__resize(size)

        self.lock.release()
    
    def __getitem__(self, key):
        self.lock.acquire()
        index = self.__get_index(key)
        entry = self.__entries[index]
        if entry:
            _, _, value = entry
            self.lock.release()
            return value
        else:
            self.lock.release()
            raise KeyError(key)
    
    def __delitem__(self, key, index=None):
        self.lock.acquire()
        index = index if index is not None else self.__get_index(key)
        if self.__entries[index]:
            self.__entries[index] = _Dummy()
        else:
            self.lock.release()
            raise KeyError(key)
        
        if len(self) < self.__prev_size * (2.0/3.0) and self.__size > self.__BASE_SIZE:
            self.__shrink()
        
        self.lock.release()

    # getattr, setattr and delattr: we are now in control of the dot :D
    def __getattr__(self, key):
        return self[key]
    
    def __setattr__(self, name, value):
        global _dict_counter, _dict_local_vars
        
        if _dict_counter < _dict_local_vars:
            self.__dict__[name] = value
        elif _dict_counter >= _dict_local_vars:
            self[name] = value
    
        _dict_counter += 1

    def __delattr__(self, key):
        del self[key] 
    
    def __iter__(self):
        for _, key, _ in self.__get_entries():
            yield key
    
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
        if type(other) is Dictionary:
            dicts = zip(self, other)
            return all(key1==key2 and self[key1]==other[key2] 
                       for key1, key2 in dicts)
        else:
            return False
    
    def __hash__(self):
        cls = self.__class__.__name__
        raise TypeError("unhashable type: '{}'".format(cls))

    def clear(self):
        self.__init__()

    def copy(self):
        cpy = Dictionary()
        for key, value in self.items():
            cpy[key] = value
        return cpy

    def get(self, key, default=None):
        index = self.__get_index(key)
        entry = self.__entries[index]
        if entry:
            _, _, value = entry
            return value
        else:
            return default

    def has_key(self, key):
        return key in self
     
    def pop(self, key, default=None):
        index = self.__get_index(key)
        item = self.__entries[index]
        if item:
            _,_, value = item
            self.__delitem__(key, index=index)
            return value
        elif default:
            return default
        else:
            raise KeyError(key)
        
    def popitem(self):
        try:
            key, value = next(iter(self.items()))
            index = self.__get_index(key)
            entry = self.__entries[index]
            if entry is not None:
                self.__delitem__(key, index=index)
                return key,value
        except StopIteration:
            raise KeyError('popitem(): dictionary is empty')   
    
    def setdefault(self, key, default=None):
        index = self.__get_index(key)
        entry = self.__entries[index]
        if entry is not None:
            _, _, value = entry
            return value
        else:
            self.__setitem__(key, default, index=index)
            return default

    def update(self, other=None, **kwargs):
        if other:
            if hasattr(other, 'keys'):
                self.__insert_from_dict(other)
            else:
                self.__insert_from_sequence(other)
        self.__insert_from_dict(kwargs)
    
    def keys(self):
        return _dictionary_keys(self)

    def items(self):
        return _dictionary_items(self)
    
    def values(self):
        return _dictionary_values(self)

    def __insert_from_dict(self, other):
        for key in other:
            self[key] = other[key]

    def __insert_from_sequence(self, sequence):
        for i, pair in enumerate(sequence):
            length = len(pair)
            
            if length != 2:
                raise ValueError('dictionary update sequence element #{} has lenght {}; 2 is required'.format(i, length))
            
            key, value = pair
            self[key] = value
    
    # Returing a generator expression is the only thing that works here because 
    # later we will need it in __resize -> __add_entries where all entries from 
    # the entry table (__entries) are deletet before inserting them to the new table. 
    # Defining generator object with yield wouldn't work since the entries 
    # would already be deleted when generating the entries.
    def __get_entries(self):
        return (entry for entry in self.__entries if entry and type(entry) is not _Dummy)

    def __get_index(self, key):
        mask = self.__size-1
        key_hash = c_size_t(hash(key))
        index = key_hash.value & mask
        
        if self.__valid_index(index, key):
            return index

        i = index
        perturb = key_hash

        while True:
            i = (i << 2) + i + perturb.value + 1
            index = i & mask
            if self.__valid_index(index, key):
                return index
            perturb.value >>= 5

    def __valid_index(self, index, key):
        entry = self.__entries[index]
        if entry is None:
            return True
        elif type(entry) is _Dummy:
            return False
        
        entry_hash, entry_key, _ = entry
        return entry_hash == hash(key) and entry_key == key

    def __resize(self, size):
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        
        # Checks if dictionary really need to resize
        # or just have to get rid of Dummy entries
        if len(self) >= (len(self.__entries) * (2.0/3.0)):
            _dict_local_vars = 3
            if size < 50000:
                    self.__size *= 4
                    prev = self.__prev_size/4
                    self.__prev_size = prev if prev > self.__BASE_SIZE else self.__BASE_SIZE
                    self.__n += 2
            else:
                    self.__size *= 2
                    self.__prev_size /= 2
                    self.__n += 1
        else:
            _dict_local_vars = 1
        
        self.__add_entries()
        
    def __shrink(self):
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        shrink = True
        if len(self) < 50000 and self.__size > self.__BASE_SIZE:
            _dict_local_vars = 2
            self.__size = self.__size/4
            self.__n -= 2
        elif len(self) >= 50000:
            _dict_local_vars = 2
            size = self.__size/2
            self.__n -= 1
        else:
            shrink = False

        if shrink:
            self.__add_entries()

    def __add_entries(self):
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        _dict_local_vars = 1
        entries = self.__get_entries()
        self.__entries = [None] * self.__size
        
        for _, key, value in entries:
            self[key] = value

    
