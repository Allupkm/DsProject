import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyodbc
from dotenv import load_dotenv
import os
import sys
import subprocess

load_dotenv()  # Point to backend's .env

class ExamManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Management System - Admin Console")
        self.root.geometry("1000x700")

        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        self.driver = '{ODBC Driver 17 for SQL Server}'
        
        self.conn = None
        self.cursor = None
        
        self.create_widgets()
        
        self.initialize_database()
        self.start_flask_backend()
    
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.db_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.db_tab, text="Database Admin")

        ttk.Label(self.db_tab, text="Select Table:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.table_var = tk.StringVar()
        self.table_combobox = ttk.Combobox(self.db_tab, textvariable=self.table_var, width=30)
        self.table_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(self.db_tab, text="Refresh Tables", command=self.refresh_tables).grid(row=0, column=2, padx=5, pady=5)

        self.tree = ttk.Treeview(self.db_tab)
        self.tree.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        yscroll = ttk.Scrollbar(self.db_tab, orient=tk.VERTICAL, command=self.tree.yview)
        yscroll.grid(row=1, column=3, sticky=tk.NS)
        xscroll = ttk.Scrollbar(self.db_tab, orient=tk.HORIZONTAL, command=self.tree.xview)
        xscroll.grid(row=2, column=0, columnspan=3, sticky=tk.EW)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        btn_frame = ttk.Frame(self.db_tab)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)
        ttk.Button(btn_frame, text="Add Record", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Record", command=self.update_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Record", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        
        self.console_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.console_tab, text="System Console")
        
        self.console = scrolledtext.ScrolledText(self.console_tab, wrap=tk.WORD, width=120, height=30)
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.insert(tk.END, "System initialized...\n")
        
        self.db_tab.rowconfigure(1, weight=1)
        self.db_tab.columnconfigure(0, weight=1)
        self.db_tab.columnconfigure(1, weight=1)
    
    def connect_to_db(self):
        try:
            self.conn = pyodbc.connect(
                f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}"
            )
            self.cursor = self.conn.cursor()
            self.log("Successfully connected to database")
            return True
        except Exception as e:
            self.log(f"Database connection failed: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect to database:\n{str(e)}")
            return False
    
    def initialize_database(self):
        if not self.connect_to_db():
            return
        
        try:
            self.cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                BEGIN
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
                    
                    -- Create other tables similarly...
                    
                    -- Add admin user if not exists
                    IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
                    BEGIN
                        INSERT INTO users (username, password_hash, salt, email, first_name, last_name, role)
                        VALUES ('admin', 'hashed_password', 'salt_value', 'admin@example.com', 'System', 'Admin', 'admin')
                    END
                    
                    PRINT 'Database tables created successfully'
                END
                ELSE
                BEGIN
                    PRINT 'Database already initialized'
                END
            """)
            self.conn.commit()
            self.log("Database initialization complete")
            self.refresh_tables()
        except Exception as e:
            self.log(f"Database initialization failed: {str(e)}")
            messagebox.showerror("Initialization Error", f"Failed to initialize database:\n{str(e)}")
    
    def refresh_tables(self):
        try:
            self.cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE'")
            tables = [row.table_name for row in self.cursor.fetchall()]
            self.table_combobox['values'] = tables
            if tables:
                self.table_var.set(tables[0])
                self.load_table_data()
            self.log(f"Refreshed table list: {len(tables)} tables found")
        except Exception as e:
            self.log(f"Error refreshing tables: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh tables:\n{str(e)}")
    
    def load_table_data(self):
        table_name = self.table_var.get()
        if not table_name:
            return
            
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            self.cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
            columns = [column[0] for column in self.cursor.description]
            self.tree['columns'] = columns
            
            
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor=tk.W)
            

            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.cursor.fetchall()
            

            for row in rows:
                self.tree.insert('', tk.END, values=row)
                
            self.log(f"Loaded {len(rows)} records from {table_name}")
        except Exception as e:
            self.log(f"Error loading table data: {str(e)}")
            messagebox.showerror("Error", f"Failed to load data:\n{str(e)}")
    
    def add_record(self):
        
        pass
    
    def update_record(self):
        
        pass
    
    def delete_record(self):
        
        pass
    
    def start_flask_backend(self):
        try:
            
            flask_process = subprocess.Popen(
                [sys.executable, "../backend/app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.log("Flask backend server started")
        except Exception as e:
            self.log(f"Failed to start Flask backend: {str(e)}")
    
    def log(self, message):
        self.console.insert(tk.END, f"> {message}\n")
        self.console.see(tk.END)
        print(message)
    
    def __del__(self):
        if self.conn:
            self.conn.close()
            self.log("Database connection closed")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExamManagementSystem(root)
    root.mainloop()