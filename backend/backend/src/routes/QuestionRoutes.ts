import { Router } from 'express';
import { ConnectionPool } from 'mssql';
import Question from '../models/question';

export default class QuestionRoutes {
  public router: Router;
  private question: Question;

  constructor(pool: ConnectionPool) {
    this.router = Router();
    this.question = new Question(pool);
    this.initializeRoutes();
  }

  private initializeRoutes() {
    // Get all questions for an exam
    this.router.get('/exam/:examId', async (req, res) => {
      try {
        const questions = await this.question.getByExam(parseInt(req.params.examId));
        res.json(questions);
      } catch (error) {
        console.error('Error getting questions:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Get all questions with options for an exam
    this.router.get('/exam/:examId/with-options', async (req, res) => {
      try {
        const questions = await this.question.getByExamWithOptions(parseInt(req.params.examId));
        res.json(questions);
      } catch (error) {
        console.error('Error getting questions with options:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Create new question
    this.router.post('/', async (req, res) => {
      try {
        const newQuestion = await this.question.create(req.body);
        res.status(201).json(newQuestion);
      } catch (error) {
        console.error('Error creating question:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Add option to question
    this.router.post('/:id/options', async (req, res) => {
      try {
        const option = { ...req.body, question_id: parseInt(req.params.id) };
        const newOption = await this.question.addOption(option);
        res.status(201).json(newOption);
      } catch (error) {
        console.error('Error adding question option:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Get question by ID with options
    this.router.get('/:id/with-options', async (req, res) => {
      try {
        const question = await this.question.getWithOptions(parseInt(req.params.id));
        if (question) {
          res.json(question);
        } else {
          res.status(404).json({ message: 'Question not found' });
        }
      } catch (error) {
        console.error('Error getting question:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Update question
    this.router.put('/:id', async (req, res) => {
      try {
        const updatedQuestion = await this.question.update(
          parseInt(req.params.id),
          req.body
        );
        if (updatedQuestion) {
          res.json(updatedQuestion);
        } else {
          res.status(404).json({ message: 'Question not found' });
        }
      } catch (error) {
        console.error('Error updating question:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Update question option
    this.router.put('/options/:optionId', async (req, res) => {
      try {
        const updatedOption = await this.question.updateOption(
          parseInt(req.params.optionId),
          req.body
        );
        if (updatedOption) {
          res.json(updatedOption);
        } else {
          res.status(404).json({ message: 'Option not found' });
        }
      } catch (error) {
        console.error('Error updating option:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Delete question
    this.router.delete('/:id', async (req, res) => {
      try {
        const success = await this.question.delete(parseInt(req.params.id));
        if (success) {
          res.json({ message: 'Question deleted successfully' });
        } else {
          res.status(404).json({ message: 'Question not found' });
        }
      } catch (error) {
        console.error('Error deleting question:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Delete question option
    this.router.delete('/options/:optionId', async (req, res) => {
      try {
        const success = await this.question.deleteOption(parseInt(req.params.optionId));
        if (success) {
          res.json({ message: 'Option deleted successfully' });
        } else {
          res.status(404).json({ message: 'Option not found' });
        }
      } catch (error) {
        console.error('Error deleting option:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });
  }
}