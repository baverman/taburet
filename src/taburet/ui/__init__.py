import flask

class Event(object):
    def __init__(self, id, event):
        self.id = id
        self.event = event
        self.actions = []
        
    def do(self, action):
        '''
        Assignd action to event
        
        @param action: Action
        @return: Event
        '''
        
        if callable(action):
            action = action()
        
        self.actions.append(action)
        
        return self
        
    def as_jsonable(self):
        return {'id':self.id, 'event':self.event,
            'actions':[r.as_jsonable() for r in self.actions]}


class Action(object):
    def __init__(self, id, action):
        self.id = id
        self.action = action
    
    def as_jsonable(self):
        return {'id':self.id, 'action':self.action }
    

class Window(object):
    def __init__(self):
        self.widgets = []
        self.events = []
        
    def as_jsonable(self):
        return {
            'widgets':[r.as_jsonable() for r in self.widgets],
            'events':[r.as_jsonable() for r in self.events]
        }

    def add(self, widget):
        self.widgets.append(widget)
        
    def on(self, event):
        '''
        Assigns event to window
        
        @param event: Event
        @return: Event
        '''
        
        if callable(event):
            event = event()
            
        self.events.append(event)
        return event


class TreeViewControl(object):
    def __init__(self, id, datasource):
        self.datasource = datasource
        self.id = id
        self.root_title = 'Root'
    
    def as_jsonable(self):
        return {
            '_type': 'TreeViewControl',
            'id': self.id,
            'datasource': self.datasource.as_jsonable(),
            'root_title': self.root_title,
        }
        
    def selected_event(self):
        return Event(self.id, 'selected')
    

class TreeViewEndpointDataSource(object):
    
    def __init__(self, endpoint):
        self.endpoint = endpoint
        
    def as_jsonable(self):
        return {'_type':'TreeViewEndpointDataSource', 'endpoint':self.endpoint}
    

class Form(object):
    def __init__(self, id, endpoint, fields=[]):
        self.id = id
        self.endpoint = endpoint
        self.fields = fields
        
    def as_jsonable(self):
        return {'_type':'Form', 'id':self.id, 'endpoint':self.endpoint,
            'fields':[r.as_jsonable() for r in self.fields]}
        
    def update_action(self):
        return Action(self.id, 'update')


class TextField(object):
    def __init__(self, id, label):
        self.id = id
        self.label = label

    def as_jsonable(self):
        return {'_type':'TextField', 'id':self.id, 'label':self.label}


def jsonify(*args, **kwargs):
    if len(args) == 1 and not kwargs:
        data = args[0]
        
        if hasattr(data, 'as_jsonable'):
            data = data.as_jsonable()
    else:
        data = kwargs
        
    return flask.Response(flask.json.dumps(data), mimetype='application/json') 