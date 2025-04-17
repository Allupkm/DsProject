from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Many-to-many relationship table for course enrollments
course_students = Table(
    'course_students', 
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    FirstName = Column(String(100), nullable=False)
    LastName = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    role = Column(String(20), nullable=False)  # admin, student, professor
    
    # Relationships
    courses_teaching = relationship("Course", back_populates="professor")
    courses_enrolled = relationship("Course", 
                                  secondary=course_students,
                                  back_populates="enrolled_students")