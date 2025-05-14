import { Router } from 'express';
import { ConnectionPool } from 'mssql';
import Course from '../models/course';

export default class CourseRoutes {
  public router: Router;
  private course: Course;

  constructor(pool: ConnectionPool) {
    this.router = Router();
    this.course = new Course(pool);
    this.initializeRoutes();
  }

  private initializeRoutes() {
    // Get all courses
    this.router.get('/', async (req, res) => {
      try {
        const includeInactive = req.query.includeInactive === 'true';
        const courses = await this.course.getAll(includeInactive);
        res.json(courses);
      } catch (error) {
        console.error('Error getting courses:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Get courses by instructor
    this.router.get('/instructor/:userId', async (req, res) => {
      try {
        const courses = await this.course.getByInstructor(parseInt(req.params.userId));
        res.json(courses);
      } catch (error) {
        console.error('Error getting instructor courses:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Get enrolled courses for a student
    this.router.get('/student/:userId', async (req, res) => {
      try {
        const courses = await this.course.getEnrolledCourses(parseInt(req.params.userId));
        res.json(courses);
      } catch (error) {
        console.error('Error getting enrolled courses:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Create new course
    this.router.post('/', async (req, res) => {
      try {
        const newCourse = await this.course.create(req.body);
        res.status(201).json(newCourse);
      } catch (error) {
        console.error('Error creating course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Get course by ID
    this.router.get('/:id', async (req, res) => {
      try {
        const course = await this.course.getById(parseInt(req.params.id));
        if (course) {
          res.json(course);
        } else {
          res.status(404).json({ message: 'Course not found' });
        }
      } catch (error) {
        console.error('Error getting course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Update course
    this.router.put('/:id', async (req, res) => {
      try {
        const updatedCourse = await this.course.update(
          parseInt(req.params.id),
          req.body
        );
        if (updatedCourse) {
          res.json(updatedCourse);
        } else {
          res.status(404).json({ message: 'Course not found' });
        }
      } catch (error) {
        console.error('Error updating course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Enroll student in course
    this.router.post('/:id/enroll', async (req, res) => {
      try {
        const { userId, role } = req.body;
        const success = await this.course.enrollStudent(
          parseInt(req.params.id),
          userId,
          role || 'student'
        );
        if (success) {
          res.json({ message: 'Enrollment successful' });
        } else {
          res.status(400).json({ message: 'Enrollment failed' });
        }
      } catch (error) {
        console.error('Error enrolling student:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Delete course (soft delete)
    this.router.delete('/:id', async (req, res) => {
      try {
        const success = await this.course.delete(parseInt(req.params.id));
        if (success) {
          res.json({ message: 'Course deleted successfully' });
        } else {
          res.status(404).json({ message: 'Course not found' });
        }
      } catch (error) {
        console.error('Error deleting course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });
  }
}