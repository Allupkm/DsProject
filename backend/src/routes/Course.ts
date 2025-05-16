import { Router, Request, Response } from 'express';
import { ConnectionPool } from 'mssql';
import Course, { ICourse } from '../models/course';

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
    this.router.get('/', (async (req: Request, res: Response) => {
      try {
        const includeInactive = req.query.includeInactive === 'true';
        const courses = await this.course.getAll(includeInactive);
        res.json(courses);
      } catch (error) {
        console.error('Error getting courses:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Create new course
    this.router.post('/', (async (req: Request, res: Response) => {
      try {
        const courseData: ICourse = {
          course_code: req.body.course_code || req.body.code || generateCourseCode(req.body.course_name || req.body.name || ''),
          course_name: req.body.course_name || req.body.name || '',description: req.body.description || '',
          created_by: req.body.created_by || getCurrentUserId(req),is_active: req.body.is_active !== undefined ? req.body.is_active : true,};

        // Validation
        if (!courseData.course_code || !courseData.course_name || !courseData.created_by) {
          return res.status(400).json({
            message: 'Missing required fields',
            required: ['course_code/code', 'course_name/name', 'created_by'],
            received: req.body,
            mapped: courseData,
          });
        }
        try {
          const newCourse = await this.course.create(courseData);
          res.status(201).json(newCourse);
        } catch (err) {
          if (err instanceof Error && err.message === 'Course code already exists') {
            return res.status(409).json({ message: 'Course code already exists' });
          }
          throw err;
        }
      } catch (error) {
        console.error('Error creating course:', error);
        res.status(500).json({
          message: 'Internal server error',
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }) as any);

    // Get course by ID
    this.router.get('/:id', (async (req: Request, res: Response) => {
      try {
        const courseId = parseInt(req.params.id);
        if (isNaN(courseId)) {
          return res.status(400).json({ message: 'Invalid course ID' });
        }

        const course = await this.course.getById(courseId);
        if (course) {
          res.json(course);
        } else {
          res.status(404).json({ message: 'Course not found' });
        }
      } catch (error) {
        console.error('Error getting course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Update course
    this.router.put('/:id', (async (req: Request, res: Response) => {
      try {
        const courseId = parseInt(req.params.id);
        if (isNaN(courseId)) {
          return res.status(400).json({ message: 'Invalid course ID' });
        }
        const updateData: Partial<ICourse> = {
          course_code: req.body.course_code || req.body.code,
          course_name: req.body.course_name || req.body.name,
          description: req.body.description,
          is_active: req.body.is_active,
        };

        try {
          const updatedCourse = await this.course.update(courseId, updateData);
          if (updatedCourse) {
            res.json(updatedCourse);
          } else {
            res.status(404).json({ message: 'Course not found' });
          }
        } catch (err) {
          if (err instanceof Error && err.message === 'Course code already exists') {
            return res.status(409).json({ message: 'Course code already exists' });
          }
          throw err;
        }
      } catch (error) {
        console.error('Error updating course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Delete course
    this.router.delete('/:id', (async (req: Request, res: Response) => {
      try {
        const courseId = parseInt(req.params.id);
        if (isNaN(courseId)) {
          return res.status(400).json({ message: 'Invalid course ID' });
        }

        const success = await this.course.delete(courseId);
        if (success) {
          res.json({ message: 'Course deleted successfully' });
        } else {
          res.status(404).json({ message: 'Course not found' });
        }
      } catch (error) {
        console.error('Error deleting course:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);
  }
}

function generateCourseCode(courseName: string): string { // Generates a course code based on the course name
  const base = courseName.replace(/[^a-zA-Z0-9]/g, '').substring(0, 4).toUpperCase();
  const randomPart = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `${base}${randomPart}`;
}
// adds foreign key to created_by
function getCurrentUserId(req: Request): number {
  const user = (req as any).user;
  if (user && user.user_id) {
    return user.user_id;
  }
  if (req.body && req.body.created_by && typeof req.body.created_by === 'number') {
    return req.body.created_by;
  }
  return 1; // Default to admin user
}
