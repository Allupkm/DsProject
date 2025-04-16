from mongoengine import Document, StringField, IntField, DateTimeField

class User(Document):
    FirstName = StringField(required=True, max_length=100)
    LastName = StringField(required=True, max_length=100)
    password = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True, max_length=100)
    role = StringField(required=True, choices=["admin", "student", "professor"])