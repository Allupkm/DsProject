import express from 'express';
import cors from 'cors';
import { ConnectionPool } from 'mssql';
import dotenv from 'dotenv';
import cluster from 'cluster';
import os from 'os';
import UserRoutes from './src/routes/UserRoutes';
import ExamRoutes from './src/routes/ExamRoutes';
import CourseRoutes from './src/routes/Course';

dotenv.config();
// gets number of CPU cores available to share the processing load
const numCPUs = os.cpus().length;
// check if clustering is enabled
const useClustering = process.env.USE_CLUSTERING === 'true';
if (useClustering && cluster.isPrimary) {
  console.log(`Master process ${process.pid} is running`);
  console.log(`Setting up ${numCPUs} workers...`);
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  cluster.on('exit', (worker, code, signal) => { // Restarts the worker if it dies
    console.log(`Worker ${worker.process.pid} died (${signal || code}). Restarting...`);
    cluster.fork();
  });
} else {
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
  const initializeDbConnection = async () => {
    try {
      poolConnection = await new ConnectionPool(dbConfig).connect();
      console.log(`Worker ${process.pid} connected to SQL Server`);
    } catch (err) {
      console.error('SQL Server connection error:', err);
      process.exit(1);
    }
  };

  // Initialize DB routes
  initializeDbConnection().then(() => {
    const userRoutes = new UserRoutes(poolConnection);
    const examRoutes = new ExamRoutes(poolConnection);
    const courseRoutes = new CourseRoutes(poolConnection);
    app.use('/api/users', userRoutes.router);
    app.use('/api/exams', examRoutes.router);
    app.use('/api/courses', courseRoutes.router);

    app.listen(PORT, HOST, () => {
      console.log(`Worker ${process.pid} is running server on http://${HOST}:${PORT}`);
    });
  });
}
