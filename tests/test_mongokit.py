from datetime import datetime

from bson import Code
from pymongo import Connection
from taburet.mongokit import Document, Field, wrap_collection

def pytest_funcarg__db(request):
    db = Connection().test
    db.collection1.drop()
    db.collection2.drop()

    return db

def test_document_must_contain_possible_fileds():
    class Doc(Document):
        f1 = Field()
        f2 = Field(required=False)

    d = Doc()
    assert d._data == {'f1':None}
    assert d._required == {'f1':None}
    assert d._unrequired == {'f2':None}

def test_document_must_contain_default_fields():
    class Doc(Document):
        f1 = Field(0)
        f2 = Field(lambda: 10)

    d = Doc()
    assert d._data['f1'] == 0
    assert d._data['f2'] == 10

def test_document_must_allow_access_by_attributes():
    class Doc(Document):
        f1 = Field(0)

    d = Doc()
    assert d.f1 == 0

    d.f1 = 'string'
    assert d.f1 == 'string'

    assert d._data['f1'] == 'string'

    del d.f1
    assert d._data == {}

def test_document_must_allow_access_by_indexes():
    class Doc(Document):
        f1 = Field(0)

    d = Doc()
    assert d['f1'] == 0

    d['f1'] = 'string'
    assert d['f1'] == 'string'
    assert 'f1' in d

    assert d._data['f1'] == 'string'

    del d['f1']
    assert d._data == {}
    assert 'f1' not in d

def test_document_creation_by_existing_data():
    class Doc(Document):
        f1 = Field(0)
        f2 = Field(10)

    d = Doc(_doc={'_id':1})
    assert d._data == {'_id':1}

def test_document_must_provide_id_attribute():
    class Doc(Document):
        pass

    d = Doc(id=1)
    assert d.id == 1

    d.id = 2
    assert d._data['_id'] == 2

def test_document_must_be_saveable(db):
    class Doc(Document):
        f1 = Field()
        f2 = Field('string')
        f3 = Field([])

        __collection__ = db.collection1

    d = Doc()
    d.save()

    dd = db.collection1.find_one({'_id':d.id})
    assert dd == d._data

    d.f1 = 10
    d.save()

    assert d.id == dd['_id']
    dd = db.collection1.find_one({'_id':d.id})
    assert dd == d._data

def test_wrap_collection(db):
    class Doc(Document):
        f = Field()

        __collection__ = db.collection1

    d1 = Doc()
    d1.f = 10
    d1.save()

    d2 = Doc()
    d2.f = 20
    d2.save()

    result = list(wrap_collection(Doc, db.collection1.find()))
    assert result[0].id == d1.id
    assert result[0].f == d1.f
    assert result[1].id == d2.id
    assert result[1].f == d2.f

def test_custom_field(db):
    class F(Field):
        def from_mongo(self, value):
            return value/10.0

        def to_mongo(self, value):
            return value*10

    class Doc(Document):
        f = F(0)

        __collection__ = db.collection1

    d = Doc(f=10).save()

    assert d.f == 10
    result = db.collection1.find_one({'_id':d.id})
    assert result['f'] == 100

def test_get_model_by_id(db):
    class Doc(Document):
        f = Field()
        __collection__ = db.collection1

    Doc(id=10, f=20).save()

    d = Doc.get(10)
    assert d.id == 10
    assert d.f == 20

def test_datetime_field(db):
    class Doc(Document):
        f = Field()
        __collection__ = db.collection1


    d1 = Doc(id=1, f=datetime(2010, 11, 1)).save()
    d2 = Doc(id=2, f=datetime(2010, 11, 15)).save()
    d3 = Doc(id=3, f=datetime(2010, 11, 30, 23, 50)).save()
    Doc(id=4, f=datetime(2010, 12, 1)).save()

    result = Doc.find({'f':{
        '$gte':datetime(2010, 11, 1),
        '$lt':datetime(2010, 12, 1)}}).list()

    assert result == [d1, d2, d3]

def test_datetime_server_processing(db):
    class Doc(Document):
        f = Field()
        __collection__ = db.collection1


    Doc(id=1, f=datetime(2010, 11, 1)).save()
    Doc(id=2, f=datetime(2010, 11, 15)).save()
    Doc(id=3, f=datetime(2010, 11, 30, 23, 50)).save()
    Doc(id=4, f=datetime(2010, 12, 1)).save()

    fmap = Code("""function() {
        var obj = this
        var dt = new Date(obj.f.getTime())
        dt.setUTCHours(0)
        dt.setUTCMinutes(0)
        dt.setUTCSeconds(0)
        dt.setUTCMilliseconds(0)
        emit(dt, 0)
    }""")

    freduce = Code("""function(key, values) {
        return 0
    }""")

    result = db.collection1.inline_map_reduce(fmap, freduce,
        query = {'f':{
            '$gte':datetime(2010, 11, 1),
            '$lt':datetime(2010, 12, 1)}})

    assert result[0]['_id'] == datetime(2010, 11, 1)
    assert result[1]['_id'] == datetime(2010, 11, 15)
    assert result[2]['_id'] == datetime(2010, 11, 30)