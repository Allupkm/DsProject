import { Router, Request, Response } from 'express';
import { ConnectionPool } from 'mssql';
import jwt from 'jsonwebtoken';
import User from '../models/user';

export default class AuthRoutes {
  public router: Router;
  private user: User;

  constructor(pool: ConnectionPool) {
    this.router = Router();
    this.user = new User(pool);
    this.initializeRoutes();
  }

  private initializeRoutes() {
    // Login route
    this.router.post('/login', (async (req: Request, res: Response) => {
      try {
        const { username, password } = req.body;
        const user = await this.user.authenticate(username, password);

        if (!user) {
          return res.status(401).json({ message: 'Invalid credentials' });
        }

        const secret = process.env.JWT_SECRET || 'your-secret-key';
        const token = jwt.sign(
          { 
            user_id: user.user_id, 
            username: user.username, 
            role: user.role 
          }, 
          secret, 
          { expiresIn: '1h' }
        );

        res.json({ token, user });
      } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Password reset request
    this.router.post('/request-reset', (async (req:Request, res:Response) => {
      try {
        const { email } = req.body;
        const user = await this.user.getByEmail(email);

        if (!user) {
          return res.status(404).json({ message: 'User not found' });
        }

        const resetToken = this.user.generateResetToken(user.user_id as number);
        // In a real app, you would send this token via email
        res.json({ resetToken });
      } catch (error) {
        console.error('Password reset error:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    })as any);

    // Password reset
    this.router.post('/reset-password', (async (req:Request, res:Response) => {
      try {
        const { token, newPassword } = req.body;
        const userId = this.user.verifyResetToken(token);

        if (!userId) {
          return res.status(400).json({ message: 'Invalid or expired token' });
        }

        const success = await this.user.changePassword(userId, newPassword);
        if (success) {
          res.json({ message: 'Password updated successfully' });
        } else {
          res.status(400).json({ message: 'Failed to update password' });
        }
      } catch (error) {
        console.error('Password reset error:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    })as any);
  }
}