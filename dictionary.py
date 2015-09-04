# This is a reimplementation of pythons built-in dictionary
# inspired by Brandon Craig Rhodes talk from PyCon 2010: The Mighty Dictionary

from threading import Lock


def bits(n):
    n += 2**32
    return bin(n)[-32:]


def dec(binary):
    return int(binary, 2)


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
    __metaclass__ = TypeReturn
    
    def __init__(self, sequence):
        global _iter_counter, _iter_local_vars
        _iter_counter = 0
        _iter_local_vars = 2
        self.__sequence = sequence
        # Hide the underscore from class name whenever printing it
        name = self.__class__.__name__
        self.__class__.__name__ = name[1:] if name.startswith('_') else name

    def __iter__(self):
        return self

    def next(self):
        return(next(self.__sequence))

    def __repr__(self):
        cls = self.__class__.__name__
        address = hex(id(self))
        return '<{} object at {}>'.format(cls, address)
    
    def __setattr__(self, name, value):
        global _iter_counter, _iter_local_vars
        _iter_counter += 1
        if _iter_counter < _iter_local_vars:
            self.__dict__[name] = value
        elif hasattr(self, name):
            self.__dict__[name] = value
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
    __metaclass__ = TypeReturn

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
    
    # Sequence must be either anther dictionary or
    # a sequece of key-value pairs so self[key] = value
    def __init__(self, sequence=None, **kwargs):
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        _dict_local_vars = 5
        self.lock = Lock()
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
        return self.__get_index(key) is not None
         
    def __setitem__(self, key, value, index=None):
        self.lock.acquire()
        index = index if index is not None else self.__get_index(key)
        self.__entries[index] = (hash(key), key, value) 

        size = self.__true_len()
        if size >= (len(self.__entries) * (2.0/3.0)):
            self.__resize(size)

        if self.lock.locked():
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
        
        if len(self) < self.__prev_size * (2.0/3.0):
            self.__shrink()
        
        if self.lock.locked():
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
        entries = self.__get_entries()
        for _, key, _ in entries:
            yield key
    
    def __repr__(self):
        items = ''
        entries = self.__get_entries()
        for _, key, value in entries:
            if type(key) is str:
                key = "'" + key + "'"
            if type(value) is str:
                value = "'" + value + "'"
            items += str(key) + ': ' + str(value) + ', '
        return '{' +  items[:-2] + '}'

    def __eq__(self, other):
        o_type = type(other)
        if o_type == Dictionary or o_type == dict:
            entries = zip(self, other)
            for key1, key2 in entries:
                if key1 != key2 or self[key1] != other[key2]:
                    return False
            return True
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
            key, value = next(self.iteritems())
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
    
    def __get_entries(self):
        return (entry for entry in self.__entries if entry and type(entry) is not _Dummy)
    
    def keys(self):
        entries = self.__get_entries()
        return [key for _, key, _ in entries]

    def items(self):
        entries = self.__get_entries()
        return [(key, value) for _, key, value in entries]

    def values(self):
        entries = self.__get_entries()
        return [value for _, _, value in entries]

    def iterkeys(self):
        _entries = self.__get_entries()
        entries = (key for _, key, _ in _entries)
        return _dictionary_keyiterator(entries)

    def iteritems(self):
        _entries = self.__get_entries()
        entries = ((key, value) for _, key, value in _entries)
        return _dictionary_itemiterator(entries)

    def itervalues(self):
        _entries = self.__get_entries()
        entries = (value for _, _, value in _entries)
        return _dictionary_valueiterator(entries)

    def viewkeys(self):
        return _dictionary_keys(self)

    def viewvalues(self):
        return _dictionary_values(self)

    def viewitems(self):
        return _dictionary_items(self)


    def __calculate_index(self, key):
        return dec(bits(hash(key))[-self.__n:])

    def __get_index(self, key):
        index = self.__calculate_index(key)
        entry = self.__entries[index]
        if entry and type(entry) is not _Dummy:
            entry_hash, entry_key, value = entry
            if entry_hash == hash(key) and entry_key == key:
                return index
        return self.__probe(index, key)
    
    def __probe(self, index, key):
        j = index
        while True:
            j = ((5*j) + 1) % 2**index
            new_index = self.__calculate_index(j)
            if self.__valid_index(new_index, key):
                return new_index
            if new_index == index:
                return self.__get_other_bits_of_hash(index, key)

    def __get_other_bits_of_hash(self, index, key):
        j = index
        perturb = hash(key)
        while True:
            j = (5*j) + 1 + perturb
            perturb <<= 5
            new_index = self.__calculate_index(j)
            if not self.__valid_index(new_index, key):
                continue
            return new_index
    
    def __valid_index(self, index, key):
        entry = self.__entries[index]
        if not self.__entries[index]:
            return True
        elif entry and type(entry) is not _Dummy:
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
        shrink = False
        if len(self) < 50000 and self.__size > self.__BASE_SIZE:
            _dict_local_vars = 2
            self.__size = self.__size/4
            self.__n -= 2
            shrink = True
        elif len(self) >= 50000:
            _dict_local_vars = 2
            size = self.__size/2
            self.__n -= 1
            shrink = True
        if shrink:
            self.__add_entries()

    def __add_entries(self):
        global _dict_counter, _dict_local_vars
        _dict_counter = 0
        _dict_local_vars = 1
        entries = self.__get_entries()
        self.__entries = [None] * self.__size
        
        for _, key, value in entries:
            if self.lock.locked():
                self.lock.release()
            self[key] = value

    

d = Dictionary(a=1, b=2, c=3)
i = d.iteritems()
