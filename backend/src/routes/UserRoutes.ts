import { Router, Request, Response, NextFunction } from 'express';
import { ConnectionPool } from 'mssql';
import bcrypt from 'bcrypt';
import User from '../models/user';

export default class UserRoutes {
  public router: Router;
  private user: User;

  constructor(pool: ConnectionPool) {
    this.router = Router();
    this.user = new User(pool);
    this.initializeRoutes();
  }
  
  private initializeRoutes() {
    // Get all users (admin only)
    this.router.get('/', async (req, res) => {
      try {
        const users = await this.user.getAllSimplified();
        res.json(users);
      } catch (error) {
        console.error('Error getting users:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    });

    // Create new user
    this.router.post('/', (async (req: Request, res: Response) => {
      try {
        const { username, email, first_name, last_name, role, password } = req.body;
        
        // Basic validation
        if (!username || !email || !first_name || !last_name || !role || !password) {
          return res.status(400).json({ message: 'All fields are required' });
        }

        if (password.length < 6) {
          return res.status(400).json({ message: 'Password must be at least 6 characters' });
        }

        // Check if username or email already exists
        const existingUserByUsername = await this.user.getByUsername(username);
        const existingUserByEmail = await this.user.getByEmail(email);
        
        if (existingUserByUsername) {
          return res.status(409).json({ message: 'Username already exists' });
        }
        
        if (existingUserByEmail) {
          return res.status(409).json({ message: 'Email already exists' });
        }

        // Create the user with is_active property
        const newUser = await this.user.create({
          username,
          email,
          first_name,
          last_name,
          role,
          is_active: true
        }, password);

        res.status(201).json(newUser);
      } catch (error) {
        console.error('Error creating user:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);
    
    // Get user by ID
    this.router.get('/:id', (async (req: Request, res: Response) => {
      try {
        const userId = parseInt(req.params.id);
        if (isNaN(userId)) {
          return res.status(400).json({ message: 'Invalid user ID' });
        }
        
        const user = await this.user.getById(userId);
        if (user) {
          res.json(user);
        } else {
          res.status(404).json({ message: 'User not found' });
        }
      } catch (error) {
        console.error('Error getting user:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Update user
    this.router.put('/:id', (async (req: Request, res: Response) => {
      try {
        const userId = parseInt(req.params.id);
        if (isNaN(userId)) {
          return res.status(400).json({ message: 'Invalid user ID' });
        }
        
        // Check if user exists
        const existingUser = await this.user.getById(userId);
        if (!existingUser) {
          return res.status(404).json({ message: 'User not found' });
        }
        
        // Check if username or email is already taken by another user
        if (req.body.username) {
          const userByUsername = await this.user.getByUsername(req.body.username);
          if (userByUsername && userByUsername.user_id !== userId) {
            return res.status(409).json({ message: 'Username already exists' });
          }
        }
        
        if (req.body.email) {
          const userByEmail = await this.user.getByEmail(req.body.email);
          if (userByEmail && userByEmail.user_id !== userId) {
            return res.status(409).json({ message: 'Email already exists' });
          }
        }
        
        const updatedUser = await this.user.update(userId, req.body);
        if (updatedUser) {
          res.json(updatedUser);
        } else {
          res.status(404).json({ message: 'User not found or no changes made' });
        }
      } catch (error) {
        console.error('Error updating user:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);

    // Change password
    this.router.post('/:id/change-password', (async (req: Request, res: Response) => {
      try {
        const { currentPassword, newPassword } = req.body;
        const userId = parseInt(req.params.id);
        if (isNaN(userId)) {
          return res.status(400).json({ message: 'Invalid user ID' });
        }

        // Verify user exists
        const user = await this.user.getById(userId);
        if (!user) {
          return res.status(404).json({ message: 'User not found' });
        }

        if (currentPassword) {
          const isMatch = await bcrypt.compare(currentPassword, user.password_hash || '');
          if (!isMatch) {
            return res.status(401).json({ message: 'Current password is incorrect' });
          }
        }

        const success = await this.user.changePassword(userId, newPassword);
        if (success) {
          res.json({ message: 'Password changed successfully' });
        } else {
          res.status(400).json({ message: 'Failed to change password' });
        }
      } catch (error) {
        console.error('Error changing password:', error);
        res.status(500).json({ message: 'Internal server error' });
      }
    }) as any);
    
    // Delete user (admin only)
    this.router.delete('/:id', (async (req: Request, res: Response) => {
      try {
        const userId = parseInt(req.params.id);
        if (isNaN(userId)) {
          return res.status(400).json({ message: 'Invalid user ID' });
        }
        
        const { success, message } = await this.user.delete(userId);
        
        if (success) {
          res.json({ message });
        } else {
          res.status(400).json({ message });
        }
      } catch (error) {
        console.error('Error deleting user:', error);
        res.status(500).json({ 
          message: 'Internal server error',
          detail: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }) as any);
  }
}
