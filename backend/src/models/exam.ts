import { ConnectionPool } from 'mssql';

export interface IExam {
  exam_id?: number;
  course_id: number;
  exam_name: string;
  description?: string;
  time_limit_minutes?: number;
  available_from?: Date;
  available_to?: Date;
  is_published?: boolean;
  created_by: number;
  created_at?: Date;
  is_active?: boolean;
  ip_restriction?: string;
  browser_lockdown?: boolean;
  show_results_immediately?: boolean;
  show_results_after?: Date;
}

export class Exam {
    constructor(private db: ConnectionPool) {}
  
    // Create a new exam
    async create(exam: IExam): Promise<IExam> {
      try {
        const result = await this.db.request()
          .input('course_id', exam.course_id)
          .input('exam_name', exam.exam_name)
          .input('description', exam.description || null)
          .input('time_limit_minutes', exam.time_limit_minutes || null)
          .input('available_from', exam.available_from || null)
          .input('available_to', exam.available_to || null)
          .input('is_published', exam.is_published || false)
          .input('created_by', exam.created_by)
          .input('is_active', exam.is_active === undefined ? true : exam.is_active)
          .input('ip_restriction', exam.ip_restriction || null)
          .input('browser_lockdown', exam.browser_lockdown || false)
          .input('show_results_immediately', exam.show_results_immediately || false)
          .input('show_results_after', exam.show_results_after || null)
          .query(`INSERT INTO exams (course_id, exam_name, description, time_limit_minutes, available_from, available_to, is_published, created_by, 
            created_at, is_active, ip_restriction, browser_lockdown, show_results_immediately, show_results_after)
            OUTPUT inserted.*VALUES (@course_id, @exam_name, @description, @time_limit_minutes,@available_from, @available_to, @is_published, @created_by,
            GETDATE(), @is_active, @ip_restriction, @browser_lockdown,@show_results_immediately, @show_results_after)`);
        return result.recordset[0];
      } catch (err) {
        console.error('Error creating exam:', err);
        throw err;
      }
    }
  
    // Get exam by ID
    async getById(examId: number): Promise<IExam | null> {
      try {
        const result = await this.db.request()
          .input('exam_id', examId)
          .query('SELECT * FROM exams WHERE exam_id = @exam_id');
        
        return result.recordset[0] || null;
      } catch (err) {
        console.error('Error getting exam by ID:', err);
        throw err;
      }
    }
  
    // Get all exams for a course
    async getByCourse(courseId: number): Promise<IExam[]> {
      try {
        const result = await this.db.request()
          .input('course_id', courseId)
          .query('SELECT * FROM exams WHERE course_id = @course_id');
        
        return result.recordset;
      } catch (err) {
        console.error('Error getting exams by course:', err);
        throw err;
      }
    }
  
    // Update an exam
    async update(examId: number, examData: Partial<IExam>): Promise<IExam | null> {
      try {
        const updates: string[] = [];
        const request = this.db.request().input('exam_id', examId);
        Object.entries(examData).forEach(([key, value]) => {
          if (key !== 'exam_id' && key !== 'created_at') {
            updates.push(`${key} = @${key}`);
            request.input(key, value);
          }
        });
        if (updates.length === 0) return null;
        const query = `UPDATE exams SET ${updates.join(', ')} OUTPUT inserted.*WHERE exam_id = @exam_id`;
        const result = await request.query(query);
        return result.recordset[0] || null;
      } catch (err) {
        console.error('Error updating exam:', err);
        throw err;
      }
    }
  
    // Publish an exam
    async publish(examId: number): Promise<boolean> {
      try {
        const result = await this.db.request()
          .input('exam_id', examId)
          .query('UPDATE exams SET is_published = 1 WHERE exam_id = @exam_id');
          
        return result.rowsAffected[0] > 0;
      } catch (err) {
        console.error('Error publishing exam:', err);
        throw err;
      }
    }
  
    // Delete an exam
    async delete(examId: number): Promise<boolean> {
      try {
        // First check if exam exists
        const exam = await this.getById(examId);
        if (!exam) {
          return false;
        }
        const result = await this.db.request()
          .input('exam_id', examId)
          .query('DELETE FROM exams WHERE exam_id = @exam_id');
          
        return result.rowsAffected[0] > 0;
      } catch (err) {
        console.error('Error deleting exam:', err);
        throw err;
      }
    }
  }
  
  export default Exam;
