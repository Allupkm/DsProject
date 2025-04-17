import sys
import os
import time
import threading
import tkinter as tk
from dotenv import load_dotenv

# Fix imports by adding parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.dirname(current_dir)  # server directory
project_dir = os.path.dirname(server_dir)  # ExamApp directory

# Add these directories to Python path
sys.path.append(server_dir)
sys.path.append(project_dir)

# Now import using absolute paths
from src.servercore import Server, DatabaseManager
from src.serverGui import ServerGUI
from models.Course import Course
from models.Exam import Exam
from models.User import User

def main():
    load_dotenv()
    useLocalDB = os.getenv("USE_LOCAL_DB", "False").lower() == "true"
    # Initialize database
    print("Initializing database connection...")
    
    db_manager = DatabaseManager(useLocalDB)
    connected = db_manager.connectToDB()
    initialized = db_manager.innitDB()
    
    if not connected or not initialized:
        print("Database initialization failed!")
        return
    
    # Initialize GUI
    print("Starting GUI...")
    root = tk.Tk()
    gui = ServerGUI(root)
    
    # Initialize and start server
    print("Starting server...")
    server = Server(db_manager)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Run GUI main loop
    print("Server is running!")
    root.mainloop()

if __name__ == "__main__":
    main()