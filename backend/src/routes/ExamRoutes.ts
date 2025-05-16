import { Router } from 'express';
import { ConnectionPool } from 'mssql';
import Exam from '../models/exam';

export default class ExamRoutes {
  public router: Router;
  private exam: Exam;

  constructor(pool: ConnectionPool) {
    this.router = Router();
    this.exam = new Exam(pool);
    this.initializeRoutes();
  }

  private initializeRoutes() {
    // Get all exams for a course
    this.router.get('/course/:courseId', async (req, res) => {
      try {
        const exams = await this.exam.getByCourse(parseInt(req.params.courseId));
        res.json(exams);
      } catch (error) {
        console.error('Error getting exams:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Create new exam
    this.router.post('/', async (req, res) => {
      try {
        const newExam = await this.exam.create(req.body);
        res.status(201).json(newExam);
      } catch (error) {
        console.error('Error creating exam:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Get exam by ID
    this.router.get('/:id', async (req, res) => {
      try {
        const exam = await this.exam.getById(parseInt(req.params.id));
        if (exam) {
          res.json(exam);
        } else {
          res.status(404).json({ message: 'Exam not found' });
        }
      } catch (error) {
        console.error('Error getting exam:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Update exam
    this.router.put('/:id', async (req, res) => {
      try {
        const updatedExam = await this.exam.update(parseInt(req.params.id),req.body);
        if (updatedExam) {
          res.json(updatedExam);
        } else {
          res.status(404).json({ message: 'Exam not found' });
        }
      } catch (error) {
        console.error('Error updating exam:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Publish exam
    this.router.post('/:id/publish', async (req, res) => {
      try {
        const success = await this.exam.publish(parseInt(req.params.id));
        if (success) {
          res.json({ message: 'Exam published successfully' });
        } else {
          res.status(404).json({ message: 'Exam not found' });
        }
      } catch (error) {
        console.error('Error publishing exam:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Delete exam
    this.router.delete('/:id', async (req, res) => {
      try {
        const success = await this.exam.delete(parseInt(req.params.id));
        if (success) {
          res.json({ message: 'Exam deleted successfully' });
        } else {
          res.status(404).json({ message: 'Exam not found' });
        }
      } catch (error) {
        console.error('Error deleting exam:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });
  }
}