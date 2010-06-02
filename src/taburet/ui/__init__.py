import flask

class Form(object):
    def __init__(self):
        self.controls = []
        
    def as_jsonable(self):
        return {'_type': 'Form', 'controls':[r.as_jsonable() for r in self.controls]}

    def add_control(self, control):
        self.controls.append(control)


class TreeViewControl(object):
    
    def __init__(self, name, datasource):
        self.datasource = datasource
        self.name = name
    
    def as_jsonable(self):
        return {
            '_type': 'TreeViewControl',
            'name': self.name,
            'datasource': self.datasource.as_jsonable()
        } 
    
class TreeViewEndpointDataSource(object):
    
    def __init__(self, endpoint):
        self.endpoint = endpoint
        
    def as_jsonable(self):
        return {'_type':'TreeViewEndpointDataSource', 'endpoint':self.endpoint}
    

def jsonify(*args, **kwargs):
    if len(args) == 1 and not kwargs:
        data = args[0]
        
        if hasattr(data, 'as_jsonable'):
            data = data.as_jsonable()
    else:
        data = kwargs
        
    return flask.Response(flask.json.dumps(data), mimetype='application/json') 