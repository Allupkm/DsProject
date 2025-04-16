import threading
import socket
import time
import logging
import pymongo
from ..models.Cources import Course
from ..models.Exam import Exam
from ..models.User import User

# This is a singleton class that manages the database connection and initialization.
class DatabaseManager:
    def __init__(self, db_name="exam_app", host="localhost", port=27017): # default values if not provided
        self.dbname = db_name
        self.host = host
        self.port = port
        self.client = None
        self.db = None
    
    def connectToDB(self): # Connect to the MongoDB server
        try:
            self.client = pymongo.MongoClient(f"mongodb://{self.host}:{self.port}/")
            self.db = self.client[self.dbname]
            logging.info(f"Connected to MongoDB at {self.host}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def innitDB(self): # Initialize the database and collections
        if not self.client:
            logging.error("Database connection not established.")
            return False
        try:
            if "Cources" not in self.db.list_collection_names():
                self.db.create_collection("Cources")
                logging.info("Cources collection created.")
            if "Exam" not in self.db.list_collection_names():
                self.db.create_collection("Exam")
                logging.info("Exam collection created.")
            if "User" not in self.db.list_collection_names():
                self.db.create_collection("User")
                logging.info("User collection created.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            return False

    def closeConnection(self): # Close the database connection
        if self.client:
            self.client.close()
            logging.info("Database connection closed.")
        else:
            logging.warning("No database connection to close.")


# Now we start creating server components
class Server:
    def __init__(self, dbManager, host='0.0.0.0', port=3000):
        self.dbManager = dbManager
        self.host = host
        self.port = port
        self.socket = None
        self.clients = []
        self.running = False
        self.thread = None
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def addConnection(self):
        pass
    
    def handleClient(self):
        pass
    