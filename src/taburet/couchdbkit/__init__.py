from couchdbkit import Property, BadValueError

from calendar import timegm
import time, datetime

class DateTimeProperty(Property):
    def __init__(self, verbose_name=None, auto_now=False, auto_now_add=False,
               **kwds):
        super(DateTimeProperty, self).__init__(verbose_name, **kwds)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        self.FORMAT = '%Y/%m/%d %H:%M:%S'

    def validate(self, value, required=True):
        value = super(DateTimeProperty, self).validate(value, required=required)

        if value is None:
            return value

        if value and not isinstance(value, self.data_type):
            raise BadValueError('Property %s must be a %s, current is %s' %
                          (self.name, self.data_type.__name__, type(value).__name__))
        return value

    def default_value(self):
        if self.auto_now or self.auto_now_add:
            return self.now()
        return Property.default_value(self)

    def to_python(self, value):
        if isinstance(value, basestring):
            try:
                timestamp = timegm(time.strptime(value, self.FORMAT))
                value = datetime.datetime.utcfromtimestamp(timestamp)
            except ValueError:
                raise ValueError('Invalid ISO date/time %r' % value)
        return value

    def to_json(self, value):
        if self.auto_now:
            value = self.now()
        
        if value is None:
            return value
        
        return value.replace(microsecond=0).strftime(self.FORMAT)

    data_type = datetime.datetime

    @staticmethod
    def now():
        return datetime.datetime.utcnow()