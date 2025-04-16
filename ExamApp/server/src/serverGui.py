import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import threading
import socket

class ServerGUI:
    def __init__(self,root):
        self.root = root
        self.root.title("Exam Application Server")
        self.root.geometry("1200x800")
        self.root.minsize(800,600)
        
        self.stats = {
            "startTime": None,
            "connections": 0,
            "exams": 0,
            "courses": 0,
            "professors": 0,
            "students": 0,
            "admins": 0,
        }
        self.uiINIT = False
        self.createwidgets()
        self.uiINIT = True
    
    def createwidgets(self):
        pass # Placeholder for the method that creates the GUI widgets
    
    def setupDashboard(self):
        pass # Placeholder for the method that sets up the dashboard UI elements
    
    def refresh(self):
        pass # Placeholder for the method that refreshes the UI elements with current data
    
    