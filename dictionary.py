# This is a reimplementation of pythons built-in dictionary
# inspired by Brandon Craig Rhodes talk from PyCon 2010: The Mighty Dictionary


def bits(n):
    n += 2**32
    return bin(n)[-32:]


def dec(binary):
    return int(binary, 2)


def calculate_index(key, n):
    return dec(bits(hash(key))[-n:])


# Dummy class for leaving a dummy value until next
# time the dictionary gets resized in case a key already has collided with
# the index where the deleted object was stored
class Dummy(object):
    def __repr__(self):
        return 'Dummy'


class __sequence_iterator(object):
    def __init__(self, sequence):
        self.sequence = sequence
        self.counter = 0

    def __iter__(self):
        return self
    
    def next(self):
        if self.counter >= len(self.sequence):
            raise StopIteration
        else:
            item = self.sequence[self.counter]
            self.counter += 1
            return item
    
    # for python3 support
    __next__ = next


class dictionary_keyiterator(__sequence_iterator):
    pass

class dictionary_valueiterator(__sequence_iterator):
    pass

class dictionary_itemiterator(__sequence_iterator):
    pass


class Dictionary(object):
    def __init__(self, mapping=None, **kwargs):
        self.__original_size = 8
        self.__size = self.__original_size
        self.__original_n = 3
        self.__n = self.__original_n
        self.entries = [None] * self.__size
        self.update(mapping, **kwargs)

    def __len__(self):
        return len([entry for entry in self.entries if entry and type(entry) is not Dummy])
    
    # also count dummy entries
    def __true_len(self):
        return len([entry for entry in self.entries if entry])

    def __contains__(self, key):
        return self.__get_index(key) is not None
    
    def __setitem__(self, key, value, index=None):
        if index:
            self.entries[index] = (hash(key), key, value)
        else:
            index = self.__get_index(key)
            self.entries[index] = (hash(key), key, value)
        
        size = self.__true_len()
        if size >= (len(self.entries) * (2.0/3.0)):
            self.__resize(size)
    
    def __getitem__(self, key):
        index = self.__get_index(key)
        if self.entries[index]:
            _, _, value = self.entries[index]
            return value
        else:
            raise KeyError(key)
    
    def __delitem__(self, key, index=None):
        if index is not None:
            self.entries[index] = Dummy()
            return
        
        index = self.__get_index(key)
        if index is not None:
            self.entries[index] = Dummy()
        else:
            raise KeyError(key) 

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
        raise TypeError('unhashable type: \'Dictionary\'')

    def clear(self):
        self.__size = self.__original_size
        self.__n = self.__original_n
        self.entries = [None] * self.__size

    def copy(self):
        cpy = Dictionary()
        for key, value in self.items():
            cpy[key] = value
        return cpy

    def get(self, key, default=None):
        index = self.__get_index(key)
        if index is not None:
            _, _, value = self.entries[index]
            return value
        return default

    def has_key(self, key):
        return key in self
    
    @classmethod
    def fromkeys(cls, seq, value=None):
        d = cls()
        for key in seq:
            d[key] = value
        return d
     
    def pop(self, key, default=None):
        index = self.__get_index(key)
        item = self.entries[index]
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
            entry = self.entries[index]
            if entry is not None:
                self.__delitem__(key, index=index)
                return key,value
        except StopIteration:
            raise KeyError('popitem(): dictionary is empty')   
    
    def setdefault(self, key, default=None):
        index = self.__get_index(key)
        entry = self.entries[index]
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
        return (entry for entry in self.entries if entry and type(entry) is not Dummy)
    
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
        entries = [key for _, key, _ in _entries]
        return dictionary_keyiterator(entries)

    def iteritems(self):
        _entries = self.__get_entries()
        entries = [(key, value) for _, key, value in _entries]
        return dictionary_itemiterator(entries)

    def itervalues(self):
        _entries = self.__get_entries()
        entries = [value for _, _, value in _entries]
        return dictionary_valueiterator(entries)

    def viewkeys(self):
        return dictionay_keys(self)

    def viewvalues(self):
        return dictionary_values(self)

    def viewitems(self):
        return dictionary_items(self)
    
    def __get_index(self, key):
        index = calculate_index(key, self.__n)
        entry = self.entries[index]
        if entry and type(entry) is not Dummy:
            entry_hash, entry_key, value = entry
            if entry_hash == hash(key) and entry_key == key:
                return index
        return self.__probe(index, key)
    
    def __probe(self, index, key):
        j = index
        while True:
            j = ((5*j) + 1) % 2**index
            new_index = calculate_index(j, self.__n)
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
            new_index = calculate_index(j, self.__n)
            if self.__valid_index(new_index, key):
                return new_index
    
    def __valid_index(self, index, key):
        entry = self.entries[index]
        if entry and type(entry) is not Dummy:
            entry_hash, entry_key, _ = entry
            if entry_hash == hash(key) and entry_key == key:
                return True
        elif not self.entries[index]:
            return True

    def __resize(self, size):
        # Checks if dictionary really need to resize
        # or just have to get rid of dummy entries
        if len(self) >= (len(self.entries) * (2.0/3.0)):
            if size < 50000:
                    self.__size *= 4
                    self.__n += 2
            else:
                    self.__size *= 2
                    self.__n += 1
        entries = self.__get_entries()
        self.entries = [None] * self.__size
        for _, key, value in entries:
            self[key] = value


