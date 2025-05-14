import express from 'express';
import path from 'path';
import cors from 'cors';
import { ConnectionPool } from 'mssql';
import dotenv from 'dotenv';
import UserRoutes from './src/routes/UserRoutes';
import ExamRoutes from './src/routes/ExamRoutes';
import QuestionRoutes from './src/routes/QuestionRoutes';
import CourseRoutes from './src/routes/Course';
import AuthRoutes from './src/routes/AuthRoutes';
import { authenticateJWT } from './src/middleware/authentication';


dotenv.config();
const app = express();

const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = process.env.HOST || '0.0.0.0';

// Middleware
app.use(cors());
app.use(express.json());

// SQL Server config
const dbConfig = {
  user: process.env.DB_USER || 'sa',
  password: process.env.DB_PASSWORD || 'YourPassword',
  database: process.env.DB_NAME || 'testdb',
  server: process.env.DB_SERVER || 'localhost',
  pool: {
    max: 10,
    min: 0,
    idleTimeoutMillis: 30000
  },
  options: {
    encrypt: true,
    trustServerCertificate: true
  }
};

// Initialize global SQL connection pool
let poolConnection: ConnectionPool;

async function initializeDbConnection() {
  try {
    poolConnection = await new ConnectionPool(dbConfig).connect();
    console.log('Connected to SQL Server');
  } catch (err) {
    console.error('SQL Server connection error:', err);
    process.exit(1);
  }
}

// Initialize DB connection
initializeDbConnection().then(() => {
  // Create route instances with the DB connection
  const authRoutes = new AuthRoutes(poolConnection);
  const userRoutes = new UserRoutes(poolConnection);
  const examRoutes = new ExamRoutes(poolConnection);
  const questionRoutes = new QuestionRoutes(poolConnection);
  const courseRoutes = new CourseRoutes(poolConnection);

  // Auth routes (no authentication required)
  app.use('/auth', authRoutes.router);

  // API routes (JWT authentication required)
  app.use('/api/users', userRoutes.router);
  app.use('/api/exams', examRoutes.router);
  app.use('/api/questions', questionRoutes.router);
  app.use('/api/courses', courseRoutes.router);

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.status(200).json({ status: 'healthy' });
  });

  app.listen(PORT, HOST, () => {
    console.log(`Server is running on http://${HOST}:${PORT}`);
  });
});