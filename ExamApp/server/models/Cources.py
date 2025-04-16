from mongoengine import Document, StringField, IntField, ListField, ReferenceField

class Course(Document):
    Coursecode = StringField(required=True, unique=True, max_length=20)
    Coursename = StringField(required=True, unique=True, max_length=100)
    description = StringField(max_length=200)
    professorID = StringField(required=True, max_length=50)
    professorName = StringField(required=True, max_length=100)
    exams = ListField(ReferenceField('Exam'), default=[]) 
    students = ListField(StringField(max_length=100), default=[])
    Active = IntField(default=1)  # 1 for active, 0 for inactive
