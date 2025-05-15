import { ConnectionPool } from 'mssql';

export interface ICourse {
  course_id?: number;
  course_code: string;
  course_name: string;
  description?: string;
  created_by: number;
  created_at?: Date;
  is_active?: boolean;
}

export interface ICourseResponse {
  id: number;
  code: string;
  name: string;
  description: string;
  created_by: number;
  is_active: boolean;
  created_at?: Date;
}

export default class Course {
  constructor(private db: ConnectionPool) {}

  async create(course: ICourse): Promise<ICourseResponse> {
    try {
      if (!course.course_code || !course.course_name || !course.created_by) {
        throw new Error('Missing required fields');
      }

      // Check if course code already exists
      const existingCourse = await this.getByCode(course.course_code);
      if (existingCourse) {
        throw new Error('Course code already exists');
      }

      const result = await this.db.request()
        .input('course_code', course.course_code)
        .input('course_name', course.course_name)
        .input('description', course.description || '')
        .input('created_by', course.created_by)
        .input('is_active', course.is_active !== undefined ? course.is_active : true)
        .query(`
          INSERT INTO courses (course_code, course_name, description, created_by, created_at, is_active)
          OUTPUT inserted.*
          VALUES (@course_code, @course_name, @description, @created_by, GETDATE(), @is_active)
        `);
      
      const insertedCourse = result.recordset[0];
      return this.formatCourseResponse(insertedCourse);
    } catch (err) {
      console.error('Error creating course:', err);
      throw err;
    }
  }
  
  // Get course by ID
  async getById(courseId: number): Promise<ICourseResponse | null> {
    try {
      const result = await this.db.request()
        .input('course_id', courseId)
        .query('SELECT * FROM courses WHERE course_id = @course_id');
      
      const course = result.recordset[0];
      return course ? this.formatCourseResponse(course) : null;
    } catch (err) {
      console.error('Error getting course by ID:', err);
      throw err;
    }
  }
  
  // Get course by code
  async getByCode(courseCode: string): Promise<ICourseResponse | null> {
    try {
      const result = await this.db.request()
        .input('course_code', courseCode)
        .query('SELECT * FROM courses WHERE course_code = @course_code');
      
      const course = result.recordset[0];
      return course ? this.formatCourseResponse(course) : null;
    } catch (err) {
      console.error('Error getting course by code:', err);
      throw err;
    }
  }
  
  // Get all active courses
  async getAll(includeInactive = false): Promise<ICourseResponse[]> {
    try {
      let query = 'SELECT * FROM courses';
      if (!includeInactive) {
        query += ' WHERE is_active = 1';
      }
      const result = await this.db.request().query(query);
      return result.recordset.map(course => this.formatCourseResponse(course));
    } catch (err) {
      console.error('Error getting all courses:', err);
      throw err;
    }
  }

  // Update a course
  async update(courseId: number, courseData: Partial<ICourse>): Promise<ICourseResponse | null> {
    try {
      // Check if course exists
      const existingCourse = await this.getById(courseId);
      if (!existingCourse) {
        return null;
      }
      
      // Check if course code is being updated and if it already exists
      if (courseData.course_code && courseData.course_code !== existingCourse.code) {
        const courseWithSameCode = await this.getByCode(courseData.course_code);
        if (courseWithSameCode) {
          throw new Error('Course code already exists');
        }
      }
      
      const updates: string[] = [];
      const request = this.db.request().input('course_id', courseId);
      
      Object.entries(courseData).forEach(([key, value]) => {
        if (key !== 'course_id' && key !== 'created_at' && value !== undefined) {
          updates.push(`${key} = @${key}`);
          request.input(key, value);
        }
      });
      
      if (updates.length === 0) return existingCourse;
      
      const query = `
        UPDATE courses 
        SET ${updates.join(', ')} 
        OUTPUT inserted.*
        WHERE course_id = @course_id
      `;
      
      const result = await request.query(query);
      const updatedCourse = result.recordset[0];
      return updatedCourse ? this.formatCourseResponse(updatedCourse) : null;
    } catch (err) {
      console.error('Error updating course:', err);
      throw err;
    }
  }

  // Get courses by instructor (created_by)
  async getByInstructor(userId: number): Promise<ICourseResponse[]> {
    try {
      const result = await this.db.request()
        .input('created_by', userId)
        .query('SELECT * FROM courses WHERE created_by = @created_by');
        
      return result.recordset.map(course => this.formatCourseResponse(course));
    } catch (err) {
      console.error('Error getting courses by instructor:', err);
      throw err;
    }
  }

  // Get enrolled courses for a student
  async getEnrolledCourses(userId: number): Promise<ICourseResponse[]> {
    try {
      const result = await this.db.request()
        .input('user_id', userId)
        .query(`
          SELECT c.* FROM courses c
          JOIN course_enrollments e ON c.course_id = e.course_id
          WHERE e.user_id = @user_id AND c.is_active = 1
        `);
        
      return result.recordset.map(course => this.formatCourseResponse(course));
    } catch (err) {
      console.error('Error getting enrolled courses:', err);
      throw err;
    }
  }

  // Check if a student is enrolled in a course
  async isEnrolled(courseId: number, userId: number): Promise<boolean> {
    try {
      const result = await this.db.request()
        .input('course_id', courseId)
        .input('user_id', userId)
        .query(`
          SELECT COUNT(*) as count FROM course_enrollments 
          WHERE course_id = @course_id AND user_id = @user_id
        `);
        
      return result.recordset[0].count > 0;
    } catch (err) {
      console.error('Error checking enrollment:', err);
      throw err;
    }
  }

  // Enroll a student in a course
  async enrollStudent(courseId: number, userId: number, role: string = 'student'): Promise<boolean> {
    try {
      // Check if course exists
      const course = await this.getById(courseId);
      if (!course) {
        throw new Error('Course not found');
      }
      
      // Check if user is already enrolled
      const alreadyEnrolled = await this.isEnrolled(courseId, userId);
      if (alreadyEnrolled) {
        throw new Error('User is already enrolled in this course');
      }
      
      const result = await this.db.request()
        .input('course_id', courseId)
        .input('user_id', userId)
        .input('role', role)
        .query(`
          INSERT INTO course_enrollments (course_id, user_id, enrollment_date, role)
          VALUES (@course_id, @user_id, GETDATE(), @role)
        `);
        
      return result.rowsAffected[0] > 0;
    } catch (err) {
      console.error('Error enrolling student:', err);
      throw err;
    }
  }

  // Delete a course (soft delete by setting is_active to false)
  async delete(courseId: number): Promise<boolean> {
    try {
      const result = await this.db.request()
        .input('course_id', courseId)
        .query('UPDATE courses SET is_active = 0 WHERE course_id = @course_id');
        
      return result.rowsAffected[0] > 0;
    } catch (err) {
      console.error('Error deleting course:', err);
      throw err;
    }
  }
  
  // Helper method to format course responses consistently
  private formatCourseResponse(course: any): ICourseResponse {
    return {
      id: course.course_id,
      code: course.course_code,
      name: course.course_name,
      description: course.description || '',
      created_by: course.created_by,
      is_active: course.is_active || false,
      created_at: course.created_at
    };
  }
}
