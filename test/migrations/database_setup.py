import pyodbc
import os
from dotenv import load_dotenv
import hashlib
import secrets

# Load environment variables
load_dotenv()

# Database connection
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

def create_tables():
    conn = None
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        cursor.execute("ALTER DATABASE CURRENT SET ALLOW_SNAPSHOT_ISOLATION ON")
        cursor.execute("ALTER DATABASE CURRENT SET READ_COMMITTED_SNAPSHOT ON")
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
        CREATE TABLE users (
            user_id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(50) UNIQUE NOT NULL,
            password_hash NVARCHAR(255) NOT NULL,
            salt NVARCHAR(255) NOT NULL,
            email NVARCHAR(100) UNIQUE NOT NULL,
            first_name NVARCHAR(50) NOT NULL,
            last_name NVARCHAR(50) NOT NULL,
            role NVARCHAR(20) CHECK (role IN ('admin', 'professor', 'student')) NOT NULL,
            is_active BIT DEFAULT 1,
            last_login DATETIME,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='courses' AND xtype='U')
        CREATE TABLE courses (
            course_id INT IDENTITY(1,1) PRIMARY KEY,
            course_code NVARCHAR(20) UNIQUE NOT NULL,
            course_name NVARCHAR(100) NOT NULL,
            description NVARCHAR(500),
            created_by INT FOREIGN KEY REFERENCES users(user_id),
            created_at DATETIME DEFAULT GETDATE(),
            is_active BIT DEFAULT 1
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='course_enrollments' AND xtype='U')
        CREATE TABLE course_enrollments (
            enrollment_id INT IDENTITY(1,1) PRIMARY KEY,
            course_id INT FOREIGN KEY REFERENCES courses(course_id),
            user_id INT FOREIGN KEY REFERENCES users(user_id),
            enrollment_date DATETIME DEFAULT GETDATE(),
            role NVARCHAR(20) CHECK (role IN ('professor', 'student', 'ta')) NOT NULL,
            UNIQUE (course_id, user_id)
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='exams' AND xtype='U')
        CREATE TABLE exams (
            exam_id INT IDENTITY(1,1) PRIMARY KEY,
            course_id INT FOREIGN KEY REFERENCES courses(course_id),
            exam_name NVARCHAR(100) NOT NULL,
            description NVARCHAR(500),
            time_limit_minutes INT,
            available_from DATETIME,
            available_to DATETIME,
            is_published BIT DEFAULT 0,
            created_by INT FOREIGN KEY REFERENCES users(user_id),
            created_at DATETIME DEFAULT GETDATE(),
            is_active BIT DEFAULT 1,
            ip_restriction NVARCHAR(255),
            browser_lockdown BIT DEFAULT 0,
            show_results_immediately BIT DEFAULT 0,
            show_results_after DATETIME
        )
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='questions' AND xtype='U')
        CREATE TABLE questions (
            question_id INT IDENTITY(1,1) PRIMARY KEY,
            exam_id INT FOREIGN KEY REFERENCES exams(exam_id),
            question_text NVARCHAR(MAX) NOT NULL,
            question_type NVARCHAR(20) CHECK (question_type IN ('multiple_choice', 'true_false', 'short_answer', 'essay')) NOT NULL,
            points DECIMAL(5,2) NOT NULL,
            display_order INT NOT NULL,
            media_url NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='question_options' AND xtype='U')
        CREATE TABLE question_options (
            option_id INT IDENTITY(1,1) PRIMARY KEY,
            question_id INT FOREIGN KEY REFERENCES questions(question_id),
            option_text NVARCHAR(MAX) NOT NULL,
            is_correct BIT DEFAULT 0,
            display_order INT NOT NULL
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='exam_attempts' AND xtype='U')
        CREATE TABLE exam_attempts (
            attempt_id INT IDENTITY(1,1) PRIMARY KEY,
            exam_id INT FOREIGN KEY REFERENCES exams(exam_id),
            user_id INT FOREIGN KEY REFERENCES users(user_id),
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            submission_time DATETIME,
            ip_address NVARCHAR(50),
            status NVARCHAR(20) CHECK (status IN ('in_progress', 'submitted', 'graded', 'archived')) DEFAULT 'in_progress',
            total_score DECIMAL(5,2),
            is_auto_submitted BIT DEFAULT 0
        )
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='answers' AND xtype='U')
        CREATE TABLE answers (
            answer_id INT IDENTITY(1,1) PRIMARY KEY,
            attempt_id INT FOREIGN KEY REFERENCES exam_attempts(attempt_id),
            question_id INT FOREIGN KEY REFERENCES questions(question_id),
            answer_text NVARCHAR(MAX),
            selected_option_id INT FOREIGN KEY REFERENCES question_options(option_id),
            points_awarded DECIMAL(5,2),
            feedback NVARCHAR(MAX),
            graded_by INT FOREIGN KEY REFERENCES users(user_id),
            graded_at DATETIME
        )
        """)

        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='archived_exams' AND xtype='U')
        CREATE TABLE archived_exams (
            archive_id INT IDENTITY(1,1) PRIMARY KEY,
            exam_id INT,
            course_id INT,
            exam_name NVARCHAR(100),
            exam_data NVARCHAR(MAX),  -- JSON representation of exam and results
            archived_by INT FOREIGN KEY REFERENCES users(user_id),
            archived_at DATETIME DEFAULT GETDATE(),
            archive_reason NVARCHAR(100)
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='audit_logs' AND xtype='U')
        CREATE TABLE audit_logs (
            log_id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT FOREIGN KEY REFERENCES users(user_id),
            action NVARCHAR(100) NOT NULL,
            entity_type NVARCHAR(50),
            entity_id INT,
            old_values NVARCHAR(MAX),
            new_values NVARCHAR(MAX),
            ip_address NVARCHAR(50),
            user_agent NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        )
        """)
        
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='heartbeats' AND xtype='U')
        CREATE TABLE heartbeats (
            heartbeat_id INT IDENTITY(1,1) PRIMARY KEY,
            component NVARCHAR(50) NOT NULL,
            status NVARCHAR(20) NOT NULL,
            timestamp DATETIME DEFAULT GETDATE(),
            message NVARCHAR(255)
        )
        """)
        
        cursor.execute("CREATE INDEX idx_course_enrollments_user ON course_enrollments(user_id)")
        cursor.execute("CREATE INDEX idx_course_enrollments_course ON course_enrollments(course_id)")
        cursor.execute("CREATE INDEX idx_exams_course ON exams(course_id)")
        cursor.execute("CREATE INDEX idx_questions_exam ON questions(exam_id)")
        cursor.execute("CREATE INDEX idx_attempts_exam_user ON exam_attempts(exam_id, user_id)")
        cursor.execute("CREATE INDEX idx_answers_attempt ON answers(attempt_id)")
        
        cursor.execute("""
        CREATE OR ALTER PROCEDURE sp_archive_old_exams
            @days_old INT = 30
        AS
        BEGIN
            SET NOCOUNT ON;
            
            BEGIN TRANSACTION;
            BEGIN TRY
                -- Archive exam attempts older than specified days
                INSERT INTO archived_exams (exam_id, course_id, exam_name, exam_data, archived_by, archive_reason)
                SELECT e.exam_id, e.course_id, e.exam_name, 
                       (SELECT * FROM exam_attempts ea 
                        JOIN answers a ON ea.attempt_id = a.attempt_id
                        WHERE ea.exam_id = e.exam_id AND ea.status = 'graded'
                        FOR JSON PATH) AS exam_data,
                       1, 'Automatic archive after ' + CAST(@days_old AS NVARCHAR) + ' days'
                FROM exams e
                JOIN exam_attempts ea ON e.exam_id = ea.exam_id
                WHERE ea.submission_time < DATEADD(day, -@days_old, GETDATE())
                AND ea.status = 'graded'
                AND NOT EXISTS (SELECT 1 FROM archived_exams ae WHERE ae.exam_id = e.exam_id);
                
                -- Update status of archived attempts
                UPDATE exam_attempts
                SET status = 'archived'
                WHERE submission_time < DATEADD(day, -@days_old, GETDATE())
                AND status = 'graded';
                
                COMMIT TRANSACTION;
            END TRY
            BEGIN CATCH
                ROLLBACK TRANSACTION;
                THROW;
            END CATCH
        END
        """)
        
        admin_username = "admin"
        admin_password = "Admin@1234"  # Change this in production!
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', admin_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        
        cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM users WHERE username = ?)
        INSERT INTO users (username, password_hash, salt, email, first_name, last_name, role)
        VALUES (?, ?, ?, 'admin@example.com', 'System', 'Admin', 'admin')
        """, (admin_username, admin_username, password_hash, salt))
        
        conn.commit()
        print("Database tables created successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()