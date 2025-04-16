import threading
import socket
import time
import pymongo
import os

from dotenv import load_dotenv
from models.Course import Course
from models.Exam import Exam
from models.User import User

# This is a singleton class that manages the database connection and initialization.
class DatabaseManager:
    def __init__(self):
        load_dotenv()

        user = os.getenv("MONGO_USER")
        password = os.getenv("MONGO_PASS")
        cluster = os.getenv("MONGO_CLUSTER")
        db_name = os.getenv("MONGO_DB")

        self.dbname = db_name
        self.uri = (
            f"mongodb+srv://{user}:{password}@{cluster}/?tls=true"
            f"&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
        )
        self.client = None
        self.db = None

    def connectToDB(self):
        try:
            self.client = pymongo.MongoClient(self.uri)
            self.db = self.client[self.dbname]
            print("Connected to MongoDB Atlas/CosmosDB!")
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
    
    def innitDB(self): # Initialize the database and collections
        if not self.client:
            print("Database connection not established.")
            return False
        try:
            if "Cources" not in self.db.list_collection_names():
                self.db.create_collection("Cources")
                print("Cources collection created.")
            if "Exam" not in self.db.list_collection_names():
                self.db.create_collection("Exam")
                print("Exam collection created.")
            if "User" not in self.db.list_collection_names():
                self.db.create_collection("User")
                print("User collection created.")
            return True
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return False

    def closeConnection(self): # Close the database connection
        if self.client:
            self.client.close()
            print("Database connection closed.")
        else:
            print("No database connection to close.")


# Now we start creating server components
class Server:
    def __init__(self,dbmanager ,host='0.0.0.0', port=3000):
        self.dbmanager = dbmanager
        self.host = host
        self.port = port
        self.socket = None
        self.clients = []
        self.running = False
        self.thread = None
        self.checkInterval = 30 # Check every 30 seconds
        self.timeout = 900 # 15 minutes timeout for client inactivity
    
    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            self.running = True
            
            self.thread = threading.Thread(target=self.addConnection)
            self.thread.daemon = True  # Daemonize thread
            self.thread.start()
            print(f"Server started on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def checkClientConnections(self):
        while self.running:
            time.sleep(self.checkInterval)
            currentTime = time.time()
            ClientsToRemove = []
            #for clientSocket in self.clients: Needs to be implemented when other functions are implemented
            #    Sends ping to client and waits for response if no response within x seconds add to ClientsToRemove
            
            
            #for client in ClientsToRemove:
            #    Send message to client to notify them of disconnection
            #    Disconnect Client and remove from list


    
    def checkDatabaseConnection(self):
        while self.running:
            time.sleep(self.checkInterval)
            currentTime = time.time()
            # Check if the database connection is still alive
            # if there is no connection to the database, try to reconnect
            # if this doesn't work, restart the server and start again
            # if the isn't anything for 5 tries, then exit the server and print txt file with the errors
    
    def stop(self):
        self.running = False
        for clientSocket in self.clients:
            try:
                clientSocket.close()
                print("Client socket closed.")
            except Exception as e:
                print(f"Error closing client socket: {e}")
        if self.socket:
            try:
                self.socket.close()
                print("Server socket closed.")
            except Exception as e:
                print(f"Error closing server socket: {e}")

    
    def addConnection(self):
        while self.running:
            try:
                ClientSocket, ClientAddress = self.socket.accept()
                print(f"Connection from {ClientAddress} has been established.")
                ClientThread= threading.Thread(target=self.handleClient, args=(ClientSocket,ClientAddress))
                ClientThread.daemon = True  # Daemonize thread
                ClientThread.start()
                self.clients.append(ClientSocket, ClientAddress,ClientThread)
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                
    def authenticate(self):
        # This handles the authentication process, checks if the user is in the database and if the password is correct additionally encryption
        # Not implemented yet
        pass
    
    def encrypt(self):
        # This handles the encryption process
        # Not implemented yet
        pass
    
    def handleClient(self):
       # This handles the client communication between client and server
       # Not implemented yet
        pass
    
    def sendMessage(self):
        # This sends a message to the client, depending on the type of message, errors, success, etc.
        pass
    
    def receiveMessage(self):
        # This receives a message from the client, depending on the type of message, errors, success, etc.
        pass
    
    def Login(self):
        # This handles the login process, checks if the user is in the database and if the password is correct additionally encryption
        # Not implemented yet
        pass
    
    def Register(self):
        # This handles the registration process, checks if the user is already in the database and if the password is correct additionally encryption
        # Not implemented yet
        pass
    
    def logout(self):
        # This handles the logout process, checks if the user is in the database and if the password is correct additionally encryption
        # Not implemented yet
        pass
    
    def CreateExam(self):
        # This handles the creation of an exam,checks if the user can create an exam and if the exam is valid, it can have multiple questions, answers, etc. points per question, etc.
        # multiple choice, true/false, etc.
        # Not implemented yet
        pass
    
    def CreateCourse(self):
        #This handles the creation of a course, checks if the user can create a course and if the course is valid
        # This is used to bind exams to courses and users to courses, where professors can create exams and students can take them
        # Not implemented yet 
        pass
    
    def GetExams(self):
        # This gets the exams from the database, checks if the user can see the exams and if the exams are valid, and if the user is in the course etc
        # Not implemented yet
        pass
    
    def GetCourses(self):
        # This gets the courses from the database, checks if the user can see the courses and if the courses are valid, and if the user is in the course etc
        # Not implemented yet
        pass
    def GetUsers(self):
        # This gets the users from the database, checks if the user can see the users and if the users are valid, and if the user is in the course etc
        # ONLY ADMIN CAN SEE THIS ALL USERS AND PROFESSORS CAN SEE STUDENTS THAT ARE IN THEIR COURSES
        # Not implemented yet
        pass
    
    def GradeExam(self):
        # This grades the exam, checks if the user can grade the exam and if the exam is valid, and if the user is in the course etc
        # Is automatically graded if the exam is multiple choice, true/false, etc. if auto check is enabled
        # Not implemented yet
        pass
    def GetResults(self):
        # This gets the results from the database, checks if the user can see the results and if the results are valid, and if the user is in the course etc
        # Not implemented yet
        pass
    