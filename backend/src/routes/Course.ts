import { Router, Request, Response } from 'express';
import { ConnectionPool } from 'mssql';
import Course, { ICourse } from '../models/course';

interface CreateCourseRequestBody {
  name?: string;            // Added support for 'name' field
  course_name?: string;     // Original field
  course_code?: string;     // Original field
  code?: string;            // Added support for 'code' field
  description?: string;
  created_by?: number;
  is_active?: boolean;
}

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

    // Get courses by instructor
    this.router.get('/instructor/:userId', (async (req: Request, res: Response) => {
      try {
        const userId = parseInt(req.params.userId);
        if (isNaN(userId)) {
          return res.status(400).json({ message: 'Invalid user ID' });
        }
        
        const courses = await this.course.getByInstructor(userId);
        res.json(courses);
      } catch (error) {
        console.error('Error getting instructor courses:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Get enrolled courses for a student
    this.router.get('/student/:userId', (async (req: Request, res: Response) => {
      try {
        const userId = parseInt(req.params.userId);
        if (isNaN(userId)) {
          return res.status(400).json({ message: 'Invalid user ID' });
        }
        
        const courses = await this.course.getEnrolledCourses(userId);
        res.json(courses);
      } catch (error) {
        console.error('Error getting enrolled courses:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Create new course
    this.router.post('/', (async (req: Request, res: Response) => {
      try {
        console.log('Course creation request received:', req.body);
        
        // Handle different field naming conventions that might come from the client
        const requestData = req.body as CreateCourseRequestBody;
        
        // Map fields with client-side naming to server-side naming
        const courseData: ICourse = {
          course_code: requestData.course_code || requestData.code || generateCourseCode(requestData.name || requestData.course_name || ''),
          course_name: requestData.course_name || requestData.name || '',
          description: requestData.description || '',
          created_by: requestData.created_by || getCurrentUserId(req),
          is_active: requestData.is_active !== undefined ? requestData.is_active : true
        };
        
        // Validate required fields after mapping
        if (!courseData.course_code || !courseData.course_name || !courseData.created_by) {
          return res.status(400).json({ 
            message: 'Missing required fields',
            required: ['course_code/code', 'course_name/name', 'created_by'],
            received: req.body,
            mapped: {
              course_code: courseData.course_code,
              course_name: courseData.course_name,
              created_by: courseData.created_by
            }
          });
        }
        
        console.log('Mapped course data:', courseData);
        
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
          error: error instanceof Error ? error.message : 'Unknown error'
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
        
        // Map incoming fields similar to create endpoint
        const requestData = req.body as CreateCourseRequestBody;
        const updateData: Partial<ICourse> = {};
        
        if (requestData.course_code || requestData.code) {
          updateData.course_code = requestData.course_code || requestData.code;
        }
        
        if (requestData.course_name || requestData.name) {
          updateData.course_name = requestData.course_name || requestData.name;
        }
        
        if (requestData.description !== undefined) {
          updateData.description = requestData.description;
        }
        
        if (requestData.is_active !== undefined) {
          updateData.is_active = requestData.is_active;
        }
        
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

    // Enroll student in course
    this.router.post('/:id/enroll', (async (req: Request, res: Response) => {
      try {
        const courseId = parseInt(req.params.id);
        const { userId, role } = req.body;
        
        if (isNaN(courseId) || !userId || isNaN(parseInt(userId))) {
          return res.status(400).json({ 
            message: 'Invalid parameters',
            required: { 
              courseId: 'Must be a valid number', 
              userId: 'Must be a valid number' 
            }
          });
        }
        
        try {
          const success = await this.course.enrollStudent(
            courseId,
            parseInt(userId),
            role || 'student'
          );
          
          if (success) {
            res.json({ message: 'Enrollment successful' });
          } else {
            res.status(400).json({ message: 'Enrollment failed' });
          }
        } catch (err) {
          if (err instanceof Error) {
            if (err.message === 'Course not found') {
              return res.status(404).json({ message: 'Course not found' });
            } else if (err.message === 'User is already enrolled in this course') {
              return res.status(409).json({ message: 'User is already enrolled in this course' });
            }
          }
          throw err;
        }
      } catch (error) {
        console.error('Error enrolling student:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Delete course (soft delete)
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
function generateCourseCode(courseName: string): string {
  const base = courseName.replace(/[^a-zA-Z0-9]/g, '')
                         .substring(0, 4)
                         .toUpperCase();
  
  const randomPart = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  
  return `${base}${randomPart}`;
}
function getCurrentUserId(req: Request): number {
  const user = (req as any).user;
  if (user && user.user_id) {
    return user.user_id;
  }
  return 1;
}
