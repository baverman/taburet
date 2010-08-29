from couchdbkit import Server

class TestServer(object):
    def __init__(self):
        self.server = Server()
    
    def get_db(self, name):
        if name in self.server:
            del self.server[name]
        
        return self.server.create_db(name)   
