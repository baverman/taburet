from pymongo.errors import DuplicateKeyError

def last_id_for(coll):
    result = coll.find({}, {'_id':1}).sort('_id', -1).limit(1)

    if result.count():
        return result[0]['_id']
    else:
        return 0

def get_new_id(coll):
    return last_id_for(coll) + 1

def save_doc_with_autoincremented_id(coll, doc, before_insert=None):
    if '_id' in doc:
        return coll.save(doc, safe=True)
    else:
        while True:
            doc['_id'] = get_new_id(coll)

            if before_insert:
                before_insert()

            try:
                return coll.insert(doc, safe=True)
                break
            except DuplicateKeyError:
                pass

def save_model_with_autoincremented_id(model):
    if '_id' in model:
        model.save()
    else:
        model.id = save_doc_with_autoincremented_id(model.__class__.__collection__, model._data)

    return model