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
 // Create a new course
  async create(course: ICourse): Promise<ICourseResponse> {
    try {
      if (!course.course_code || !course.course_name || !course.created_by) { // Validation
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
        .query(`INSERT INTO courses (course_code, course_name, description, created_by, created_at, is_active)OUTPUT inserted.*
          VALUES (@course_code, @course_name, @description, @created_by, GETDATE(), @is_active)`);
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
      
      // Check if new course code exist
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
      
      const query = `UPDATE courses SET ${updates.join(', ')} OUTPUT inserted.*WHERE course_id = @course_id`;
      
      const result = await request.query(query);
      const updatedCourse = result.recordset[0];
      return updatedCourse ? this.formatCourseResponse(updatedCourse) : null;
    } catch (err) {
      console.error('Error updating course:', err);
      throw err;
    }
  }
  // Delete course, sets it as inactive
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
