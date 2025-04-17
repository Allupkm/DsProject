from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    Coursecode = Column(String(20), nullable=False, unique=True)
    Coursename = Column(String(100), nullable=False)
    description = Column(String(200))
    professorID = Column(String(50), ForeignKey('users.email'), nullable=False)
    professorName = Column(String(100), nullable=False)
    
    # Relationships
    exams = relationship("Exam", back_populates="course", cascade="all, delete-orphan")
    professor = relationship("User", back_populates="courses_teaching")
    enrolled_students = relationship("User", 
                                   secondary="course_students",
                                   back_populates="courses_enrolled")