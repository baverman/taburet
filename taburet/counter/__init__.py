import os.path
from couchdbkit import FileSystemDocsLoader, ResourceConflict, Document

def max_num_for(db, prefix):
    result = db.view('counter/max_value', key=prefix).one()
    
    if result is None:
        return 0
    else:
        return result['value']

def get_new_id(db, prefix):
    return "%s-%d" % (prefix, max_num_for(db, prefix) + 1)

def save_doc_with_autoincremented_id(doc, db, prefix):
    if '_rev' in doc:
        db.save_doc(doc)
    else:
        if '_id' not in doc:
            doc['_id'] = get_new_id(db, prefix) 
        
        while True:
            try:
                db.save_doc(doc)
                break
            except ResourceConflict:
                doc['_id'] = get_new_id(db, prefix)
                
def save_model_with_autoincremented_id(doc, prefix):
    db = doc.get_db()
    if '_rev' in doc:
        Document.save(doc)
    else:
        if '_id' not in doc:
            doc._id = get_new_id(db, prefix) 
        
        while True:
            try:
                Document.save(doc)
                break
            except ResourceConflict:
                doc._id = get_new_id(db, prefix)