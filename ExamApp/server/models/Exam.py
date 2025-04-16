from mongoengine import Document, StringField, IntField, ListField, ReferenceField
from datetime import datetime

class Exam(Document):
    ExamCode = StringField(required=True, unique=True, max_length=20)
    ExamName = StringField(required=True, max_length=100)
    description = StringField(max_length=200)
    CourseCode = StringField(required=True, max_length=20)
    CourseName = StringField(required=True, max_length=100)
    
