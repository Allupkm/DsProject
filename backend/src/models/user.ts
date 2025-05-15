import { ConnectionPool, VarChar, NVarChar, Int, DateTime, Bit } from 'mssql';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

export interface IUser {
  user_id?: number;
  username: string;
  password_hash?: string;
  salt?: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'teacher' | 'student';
  is_active?: boolean;
  last_login?: Date;
  created_at?: Date;
  updated_at?: Date;
}

export class User {
  constructor(private db: ConnectionPool) {}

  // Create a new user with password hashing
  async create(user: Omit<IUser, 'user_id' | 'password_hash' | 'salt' | 'last_login' | 'created_at' | 'updated_at'>, password: string) {
    try {
      const saltRounds = 10;
      const salt = await bcrypt.genSalt(saltRounds);
      const hashedPassword = await bcrypt.hash(password, salt);

      const result = await this.db.request()
        .input('username', NVarChar, user.username)
        .input('email', NVarChar, user.email)
        .input('first_name', NVarChar, user.first_name)
        .input('last_name', NVarChar, user.last_name)
        .input('role', NVarChar, user.role)
        .input('password_hash', NVarChar, hashedPassword)
        .input('salt', NVarChar, salt)
        .input('is_active', Bit, user.is_active !== undefined ? user.is_active : true)
        .query(`
          INSERT INTO users (username, email, first_name, last_name, role, password_hash, salt, is_active, created_at, updated_at)
          OUTPUT inserted.*
          VALUES (@username, @email, @first_name, @last_name, @role, @password_hash, @salt, @is_active, GETDATE(), GETDATE());
        `);

      const newUser = result.recordset[0];
      
      // Return without sensitive data
      const safeUser = { ...newUser };
      delete safeUser.password_hash;
      delete safeUser.salt;
      
      return safeUser;
    } catch (error) {
      console.error('Error creating user:', error);
      throw error;
    }
  }

  async getById(userId: number): Promise<IUser | null> {
    try {
      const result = await this.db.request()
        .input('user_id', Int, userId)
        .query('SELECT * FROM users WHERE user_id = @user_id');

      const user = result.recordset[0];
      if (!user) return null;

      return {
        user_id: user.user_id,
        username: user.username,
        email: user.email,
        first_name: user.first_name,
        last_name: user.last_name,
        role: user.role,
        password_hash: user.password_hash,
        salt: user.salt,
        is_active: user.is_active,
        last_login: user.last_login,
        created_at: user.created_at,
        updated_at: user.updated_at
      };
    } catch (err) {
      console.error('Error getting user by ID:', err);
      throw err;
    }
  }

  async getByUsername(username: string): Promise<IUser | null> {
    try {
      const result = await this.db.request()
        .input('username', NVarChar, username)
        .query('SELECT * FROM users WHERE username = @username');

      return result.recordset[0] || null;
    } catch (err) {
      console.error('Error getting user by username:', err);
      throw err;
    }
  }

  async getByEmail(email: string): Promise<IUser | null> {
    try {
      const result = await this.db.request()
        .input('email', NVarChar, email)
        .query('SELECT * FROM users WHERE email = @email');

      return result.recordset[0] || null;
    } catch (err) {
      console.error('Error getting user by email:', err);
      throw err;
    }
  }

  async authenticate(username: string, password: string): Promise<IUser | null> {
    try {
      const user = await this.getByUsername(username);
      if (!user || !user.password_hash) return null;

      const isMatch = await bcrypt.compare(password, user.password_hash);
      if (!isMatch) return null;

      await this.db.request()
        .input('user_id', Int, user.user_id!)
        .query('UPDATE users SET last_login = GETDATE() WHERE user_id = @user_id');

      const safeUser = { ...user };
      delete safeUser.password_hash;
      delete safeUser.salt;

      return safeUser;
    } catch (err) {
      console.error('Error authenticating user:', err);
      throw err;
    }
  }

  async delete(userId: number): Promise<{ success: boolean; message: string }> {
    try {
      // First check if the user exists
      const userExists = await this.getById(userId);
      if (!userExists) {
        return { success: false, message: 'User not found' };
      }

      // Check if the user is enrolled in any courses
      const enrollmentCheck = await this.db.request()
        .input('user_id', Int, userId)
        .query(`
          SELECT COUNT(*) as count 
          FROM course_enrollments 
          WHERE user_id = @user_id
        `);
      
      const enrollmentCount = enrollmentCheck.recordset[0].count;
      
      // Check if user has created any courses
      const courseCheck = await this.db.request()
        .input('created_by', Int, userId)
        .query(`
          SELECT COUNT(*) as count 
          FROM courses 
          WHERE created_by = @created_by
        `);
      
      const courseCount = courseCheck.recordset[0].count;

      // If there are dependencies, mark as inactive instead of deleting
      if (enrollmentCount > 0 || courseCount > 0) {
        await this.db.request()
          .input('user_id', Int, userId)
          .query('UPDATE users SET is_active = 0 WHERE user_id = @user_id');
        return { success: true, message: 'User deactivated due to existing course dependencies' };
      }
      
      // If no dependencies, proceed with deletion
      const result = await this.db.request()
        .input('user_id', Int, userId)
        .query('DELETE FROM users WHERE user_id = @user_id');
      
      return {
        success: result.rowsAffected[0] > 0,
        message: result.rowsAffected[0] > 0 ? 'User deleted successfully' : 'Failed to delete user'
      };
    } catch (err) {
      console.error('Error deleting user:', err);
      throw err;
    }
  }

  async update(userId: number, userData: Partial<IUser>): Promise<IUser | null> {
    try {
      const updates: string[] = [];
      const request = this.db.request().input('user_id', Int, userId);

      // Clean up data to prevent unwanted updates
      const cleanedData = { ...userData };
      delete cleanedData.user_id;
      delete cleanedData.password_hash;
      delete cleanedData.salt;
      delete cleanedData.created_at;
      delete cleanedData.last_login;
      delete cleanedData.updated_at;

      Object.entries(cleanedData).forEach(([key, value]) => {
        if (value !== undefined) {
          updates.push(`${key} = @${key}`);
          request.input(key, value as any);
        }
      });

      if (updates.length === 0) {
        // No updates to perform, return the current user
        return this.getById(userId);
      }
      
      updates.push('updated_at = GETDATE()');

      const result = await request.query(`
        UPDATE users 
        SET ${updates.join(', ')} 
        OUTPUT inserted.* 
        WHERE user_id = @user_id
      `);

      const user = result.recordset[0];
      if (!user) return null;

      // Return without sensitive data
      const safeUser = { ...user };
      delete safeUser.password_hash;
      delete safeUser.salt;
      
      return safeUser;
    } catch (err) {
      console.error('Error updating user:', err);
      throw err;
    }
  }

  async getAll(): Promise<IUser[]> {
    try {
      const result = await this.db.request().query('SELECT * FROM users');
      return result.recordset.map(user => {
        const safeUser = { ...user };
        delete safeUser.password_hash;
        delete safeUser.salt;
        return safeUser;
      });
    } catch (error) {
      console.error('Error fetching users:', error);
      throw error;
    }
  }

  async getAllSimplified(): Promise<{id: number, name: string, email: string, role: string}[]> {
    try {
      const users = await this.getAll();
      return users.map(u => ({
        id: u.user_id!,
        name: `${u.first_name} ${u.last_name}`,
        email: u.email,
        role: u.role
      }));
    } catch (error) {
      console.error('Error fetching simplified users:', error);
      throw error;
    }
  }

  async changePassword(userId: number, newPassword: string): Promise<boolean> {
    try {
      const saltRounds = 10;
      const salt = await bcrypt.genSalt(saltRounds);
      const passwordHash = await bcrypt.hash(newPassword, salt);

      const result = await this.db.request()
        .input('user_id', Int, userId)
        .input('password_hash', NVarChar, passwordHash)
        .input('salt', NVarChar, salt)
        .query(`
          UPDATE users 
          SET password_hash = @password_hash, salt = @salt, updated_at = GETDATE() 
          WHERE user_id = @user_id
        `);

      return result.rowsAffected[0] > 0;
    } catch (err) {
      console.error('Error changing password:', err);
      throw err;
    }
  }

  generateResetToken(userId: number): string {
    const secret = process.env.JWT_SECRET || 'your-secret-key';
    return jwt.sign({ user_id: userId }, secret, { expiresIn: '1h' });
  }

  verifyResetToken(token: string): number | null {
    try {
      const secret = process.env.JWT_SECRET || 'your-secret-key';
      const decoded = jwt.verify(token, secret) as { user_id: number };
      return decoded.user_id;
    } catch (err) {
      return null;
    }
  }
}

export default User;
