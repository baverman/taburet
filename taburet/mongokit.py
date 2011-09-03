def wrap_collection(cls, seq):
    return (cls(_doc=r) for r in seq)

def make_field_getter(name, value=None):
    if value and value.__class__ is not Field:
        return lambda self: value.from_mongo(self._data[name])
    else:
        return lambda self: self._data[name]

def make_field_setter(name, value=None):
    if value and value.__class__ is not Field:
        def inner(self, v):
            self._data[name] = value.to_mongo(v)
    else:
        def inner(self, v):
            self._data[name] = v

    return inner

def make_field_deleter(name):
    def inner(self):
        del self._data[name]

    return inner


class Meta(type):
    def __new__(mcls, cname, bases, fields):
        required = fields['_required'] = {}
        unrequired = fields['_unrequired'] = {}
        dfields = fields['_fields'] = {}

        for name, value in fields.iteritems():
            if isinstance(value, Field):
                dfields[name] = value

                if value.required:
                    required[name] = value.default
                else:
                    unrequired[name] = None

                fields[name] = property(
                    make_field_getter(name, value),
                    make_field_setter(name, value),
                    make_field_deleter(name)
                )

        fields['id'] = property(
            make_field_getter('_id'),
            make_field_setter('_id'),
            make_field_deleter('_id')
        )

        return type.__new__(mcls, cname, bases, fields)


class Field(object):
    def __init__(self, default=None, required=True):
        self.default = default
        self.required = required

    def to_mongo(self, value):
        return value

    def from_mongo(self, value):
        return value


class Currency(Field):
    def to_mongo(self, value):
        return int(round(value * 100))

    def from_mongo(self, value):
        return value/100.0


class Document(object):
    __metaclass__ = Meta

    class NotFound(Exception): pass
    class MultipleResultsFound(Exception): pass

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)

        doc = kwargs.get('_doc', None)
        if doc is None:
            obj._data = data = {}
            fields = cls._fields

            if 'id' in kwargs:
                data['_id'] = kwargs['id']

            for k, v in cls._required.iteritems():
                if k in kwargs:
                    v = kwargs[k]

                if callable(v):
                    data[k] = fields[k].to_mongo(v())
                else:
                    data[k] = fields[k].to_mongo(v)

            for k, v in cls._unrequired.iteritems():
                if k in kwargs:
                    data[k] = fields[k].to_mongo(kwargs[k])

        else:
            obj._data = doc

        return obj

    def __getitem__(self, name):
        return self._data[name]

    def __setitem__(self, name, value):
        if name in self.__class__._required or name in self.__class__._unrequired:
            self._data[name] = value
        else:
            raise KeyError(name)

    def __delitem__(self, name):
        del self._data[name]

    def __contains__(self, name):
        return name in self._data

    def __eq__(self, ob):
        if ob:
            return self.id == ob.id
        else:
            return False

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self._data)

    def save(self):
        self.id = self.__class__.__collection__.save(self._data, safe=True)
        return self

    @classmethod
    def get(cls, doc_id):
        return cls(_doc=cls.__collection__.find_one({'_id':doc_id}))

    @classmethod
    def find(cls, *args, **kwargs):
        return Cursor(cls, cls.__collection__.find(*args, **kwargs))


class Cursor(object):
    def __init__(self, cls, cursor):
        self.cls = cls
        self.cursor = cursor

    def __iter__(self):
        return wrap_collection(self.cls, self.cursor)

    def list(self):
        return list(iter(self))

    def all(self):
        return list(iter(self))

    def one(self):
        it = iter(self.cursor)
        doc = None
        try:
            doc = it.next()
            it.next()
        except StopIteration:
            if doc:
                return self.cls(_doc=doc)

            return None
        else:
            raise Document.MultipleResultsFound()