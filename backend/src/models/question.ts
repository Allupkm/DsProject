import { ConnectionPool } from 'mssql';

export interface IQuestion {
  question_id?: number;
  exam_id: number;
  question_text: string;
  question_type: 'multiple_choice' | 'true_false' | 'short_answer' | 'essay';
  points: number;
  display_order: number;
  media_url?: string;
  created_at?: Date;
}

export interface IQuestionOption {
  option_id?: number;
  question_id: number;
  option_text: string;
  is_correct: boolean;
  display_order: number;
}

export class Question {
    constructor(private db: ConnectionPool) {}
  
    // Create a new question
    async create(question: IQuestion): Promise<IQuestion> {
      try {
        const result = await this.db.request()
          .input('exam_id', question.exam_id)
          .input('question_text', question.question_text)
          .input('question_type', question.question_type)
          .input('points', question.points)
          .input('display_order', question.display_order)
          .input('media_url', question.media_url || null)
          .query(`
            INSERT INTO questions (exam_id, question_text, question_type, points, display_order, media_url, created_at)
            OUTPUT inserted.*
            VALUES (@exam_id, @question_text, @question_type, @points, @display_order, @media_url, GETDATE())
          `);
        
        return result.recordset[0];
      } catch (err) {
        console.error('Error creating question:', err);
        throw err;
      }
    }
  
    // Add an option to a multiple choice question
    async addOption(option: IQuestionOption): Promise<IQuestionOption> {
      try {
        const result = await this.db.request()
          .input('question_id', option.question_id)
          .input('option_text', option.option_text)
          .input('is_correct', option.is_correct)
          .input('display_order', option.display_order)
          .query(`
            INSERT INTO question_options (question_id, option_text, is_correct, display_order)
            OUTPUT inserted.*
            VALUES (@question_id, @option_text, @is_correct, @display_order)
          `);
        
        return result.recordset[0];
      } catch (err) {
        console.error('Error adding question option:', err);
        throw err;
      }
    }
  
    // Get question by ID
    async getById(questionId: number): Promise<IQuestion | null> {
      try {
        const result = await this.db.request()
          .input('question_id', questionId)
          .query('SELECT * FROM questions WHERE question_id = @question_id');
        
        return result.recordset[0] || null;
      } catch (err) {
        console.error('Error getting question by ID:', err);
        throw err;
      }
    }
  
    // Get question with options
    async getWithOptions(questionId: number): Promise<{ question: IQuestion, options: IQuestionOption[] } | null> {
      try {
        const questionResult = await this.db.request()
          .input('question_id', questionId)
          .query('SELECT * FROM questions WHERE question_id = @question_id');
        
        if (!questionResult.recordset[0]) return null;
        
        const optionsResult = await this.db.request()
          .input('question_id', questionId)
          .query('SELECT * FROM question_options WHERE question_id = @question_id ORDER BY display_order');
        
        return {
          question: questionResult.recordset[0],
          options: optionsResult.recordset
        };
      } catch (err) {
        console.error('Error getting question with options:', err);
        throw err;
      }
    }
  
    // Get all questions for an exam
    async getByExam(examId: number): Promise<IQuestion[]> {
      try {
        const result = await this.db.request()
          .input('exam_id', examId)
          .query('SELECT * FROM questions WHERE exam_id = @exam_id ORDER BY display_order');
        
        return result.recordset;
      } catch (err) {
        console.error('Error getting questions by exam:', err);
        throw err;
      }
    }

    async getAllSimplified(): Promise<{
      id: number, 
      questionText: string, 
      examId: number, 
      options: string, 
      correctAnswer: string
    }[]> {
      const result = await this.db.request().query(`
        SELECT q.question_id as id, q.question_text as questionText, 
        q.exam_id as examId, 
        STRING_AGG(o.option_text, ', ') as options,
        (SELECT option_text FROM question_options WHERE question_id = q.question_id AND is_correct = 1) as correctAnswer
        FROM questions q
        LEFT JOIN question_options o ON q.question_id = o.question_id
        GROUP BY q.question_id, q.question_text, q.exam_id
      `);
      return result.recordset;
    }
  
    // Get all questions with options for an exam
    async getByExamWithOptions(examId: number): Promise<{ question: IQuestion, options: IQuestionOption[] }[]> {
      try {
        const questions = await this.getByExam(examId);
        const questionsWithOptions = [];
        
        for (const question of questions) {
          const optionsResult = await this.db.request()
            .input('question_id', question.question_id)
            .query('SELECT * FROM question_options WHERE question_id = @question_id ORDER BY display_order');
          
          questionsWithOptions.push({
            question,
            options: optionsResult.recordset
          });
        }
        
        return questionsWithOptions;
      } catch (err) {
        console.error('Error getting questions with options by exam:', err);
        throw err;
      }
    }
  
    // Update a question
    async update(questionId: number, questionData: Partial<IQuestion>): Promise<IQuestion | null> {
      try {
        const updates: string[] = [];
        const request = this.db.request().input('question_id', questionId);
        
        Object.entries(questionData).forEach(([key, value]) => {
          if (key !== 'question_id' && key !== 'created_at') {
            updates.push(`${key} = @${key}`);
            request.input(key, value);
          }
        });
        
        if (updates.length === 0) return null;
        
        const query = `
          UPDATE questions 
          SET ${updates.join(', ')} 
          OUTPUT inserted.*
          WHERE question_id = @question_id
        `;
        
        const result = await request.query(query);
        return result.recordset[0] || null;
      } catch (err) {
        console.error('Error updating question:', err);
        throw err;
      }
    }
  
    // Update a question option
    async updateOption(optionId: number, optionData: Partial<IQuestionOption>): Promise<IQuestionOption | null> {
      try {
        const updates: string[] = [];
        const request = this.db.request().input('option_id', optionId);
        
        Object.entries(optionData).forEach(([key, value]) => {
          if (key !== 'option_id') {
            updates.push(`${key} = @${key}`);
            request.input(key, value);
          }
        });
        
        if (updates.length === 0) return null;
        
        const query = `
          UPDATE question_options 
          SET ${updates.join(', ')} 
          OUTPUT inserted.*
          WHERE option_id = @option_id
        `;
        
        const result = await request.query(query);
        return result.recordset[0] || null;
      } catch (err) {
        console.error('Error updating question option:', err);
        throw err;
      }
    }
  
    // Delete a question and its options
    async delete(questionId: number): Promise<boolean> {
      try {
        // First delete options
        await this.db.request()
          .input('question_id', questionId)
          .query('DELETE FROM question_options WHERE question_id = @question_id');
        
        // Then delete the question
        const result = await this.db.request()
          .input('question_id', questionId)
          .query('DELETE FROM questions WHERE question_id = @question_id');
          
        return result.rowsAffected[0] > 0;
      } catch (err) {
        console.error('Error deleting question:', err);
        throw err;
      }
    }
  
    // Delete a question option
    async deleteOption(optionId: number): Promise<boolean> {
      try {
        const result = await this.db.request()
          .input('option_id', optionId)
          .query('DELETE FROM question_options WHERE option_id = @option_id');
          
        return result.rowsAffected[0] > 0;
      } catch (err) {
        console.error('Error deleting question option:', err);
        throw err;
      }
    }
}
  
export default Question;