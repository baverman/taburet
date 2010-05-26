from couchdbkit import Property, BadValueError, DateTimeProperty as CDBKitDateTimeProperty

from calendar import timegm
import time, datetime

class DateTimeProperty(CDBKitDateTimeProperty):
    def to_python(self, value):
        if isinstance(value, (list, tuple)):
            value = datetime.datetime(*value)
        return value

    def to_json(self, value):
        if self.auto_now:
            value = self.now()
        
        if value is None:
            return value
        
        return (value.year, value.month, value.day, value.hour, value.minute, value.second)

    @staticmethod
    def now():
        return datetime.datetime.now()