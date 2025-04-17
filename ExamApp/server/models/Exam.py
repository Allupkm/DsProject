from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Exam(Base):
    __tablename__ = 'exams'
    
    id = Column(Integer, primary_key=True)
    ExamCode = Column(String(20), nullable=False, unique=True)
    ExamName = Column(String(100), nullable=False)
    description = Column(String(200))
    CourseCode = Column(String(20), ForeignKey('courses.Coursecode'), nullable=False)
    CourseName = Column(String(100), nullable=False)
    Active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    
    # Relationship to Course
    course = relationship("Course", back_populates="exams")

