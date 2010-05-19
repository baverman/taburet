from couchdbkit import Document, ListProperty, FloatProperty, DateTimeProperty, StringProperty
import datetime


class Transaction(Document):
    from_acc = ListProperty(verbose_name="From accounts", required=True)
    to_acc = ListProperty(verbose_name="To accounts", required=True)
    amount = FloatProperty(default=0.0)
    date = DateTimeProperty(default=datetime.datetime.utcnow, required=True)


class Account(Document):
    title = StringProperty()
    parents = ListProperty()