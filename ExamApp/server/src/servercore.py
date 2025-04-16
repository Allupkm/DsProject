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
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            socket.listen()
            self.running = True
            
            self.thread = threading.Thread(target=self.addConnection)
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()
            logging.info(f"Server started on {self.host}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False
        
    
    def stop(self):
        self.running = False
        for clientSocket in self.clients:
            try:
                clientSocket.close()
                logging.info("Client socket closed.")
            except Exception as e:
                logging.error(f"Error closing client socket: {e}")
        if self.socket:
            try:
                self.socket.close()
                logging.info("Server socket closed.")
            except Exception as e:
                logging.error(f"Error closing server socket: {e}")

    
    def addConnection(self):
        while self.running:
            try:
                ClientSocket, ClientAddress = self.socket.accept()
                logging.info(f"Connection from {ClientAddress} has been established.")
                ClientThread= threading.Thread(target=self.handleClient, args=(ClientSocket,ClientAddress))
                ClientThread.daemon = True  # Daemonize thread
                ClientThread.start()
                self.clients.append(ClientSocket, ClientAddress,ClientThread)
            except Exception as e:
                if self.running:
                    logging.error(f"Error accepting connection: {e}")
                
    
    def handleClient(self):
        pass
    