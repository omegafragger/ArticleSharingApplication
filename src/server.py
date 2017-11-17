#!/user/bin/python

import MySQLdb
import select
import socket
import sys
import threading
import dbauthorization
import time
import cPickle
#---------------------------------------------------------------------------------------------------
class DBHandler:
    """A class to abstract database operations for the server."""
    
    def __init__(self):
        """Constructor to initialize the username and password for database access"""
        self.username = dbauthorization.username
        self.password = dbauthorization.password

    def insert_tuple(self, clid, title, author):
        """Method to insert a single tuple in the database table"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("query1","r")
        q = fp.read(1024)
        query = q %(clid, title, author)
        cursor.execute(query)
        conn.commit()
        conn.close()
        fp.close()

    def delete_tuples(self, clid):
        """Method to delete all tuples related to a client from the database table"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("query2","r")
        q = fp.read(1024)
        query = q %(clid)
        cursor.execute(query)
        conn.commit()
        fp.close()
        conn.close()
    
    def select_all_query(self, cl, title, auth):
        """Method to select all the tuples in the database table
        The method returns three lists corresponding to the three attributes"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_selectall", "r")
        q = fp.read(1024)
        cursor.execute(query)
        s = cursor.fetchone()
        while s != None:
            cl.append(s[0])
            title.append(s[1])
            auth.append(s[2])
        fp.close()
        conn.close()
    
    def select_title_query(self, titl, cl, auth):
        """Method to select all the tuples in table having a given title titl"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_select_title", "r")
        q = fp.read(1024)
        query = q %(titl)
        cursor.execute(query)
        s = cursor.fetchone()
        while s != None:
            cl.append(s[0])
            auth.append(s[2])
            s = cursor.fetchone()
        fp.close()
        conn.close()

    def select_author_query(self, auth, cl, title):
        """Method to select all the tuples in table having a given author auth"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_select_author", "r")
        q = fp.read(1024)
        query = q %(auth)
        cursor.execute(query)
        s = cursor.fetchone()
        while s != None:
            cl.append(s[0])
            title.append(s[1])
            s = cursor.fetchone()
        fp.close()
        conn.close()

    def select_tit_auth_query(self, title, auth, cl):
        """Method to select tuples having a given author and a given title"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_select_title_author", "r")
        q = fp.read(1024)
        query = q %(title, auth)
        cursor.execute(query)
        s = cursor.fetchone()
        while s != None:
            cl.append(s[0])
            s = cursor.fetchone()
        fp.close()
        conn.close()
    
    def select_last_client(self):
        """A method to select the last client inserted into the clients table."""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_select_last_client", "r")
        q = fp.read(1024)
        cursor.execute(q)
        s = cursor.fetchone()
        res = int(s[0])
        fp.close()
        conn.close()
        return res

    def insert_client_query(self, ipaddr, port):
        """A method to insert a new client into the database and store its IP address and port number"""
        last_client = self.select_last_client()
        last_client += 1
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_insert_client", "r")
        q = fp.read(1024)
        query = q %(last_client, ipaddr, port)
        print "QUERY executed: " + query
        cursor.execute(query)
        conn.commit()
        fp.close()
        conn.close()

    def select_client_query(self, client_id):
        """A method to return client information (IP address and Port number) given a client ID"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_select_client", "r")
        q = fp.read(1024)
        query = q %(client_id)
        cursor.execute(query)
        s = cursor.fetchone()
        res = []
        res.append(s[0])
        res.append(s[1])
        fp.close()
        conn.close()
        return res
    
    def exist_clients(self):
        """A method to check if at least a single client exists"""
        conn = MySQLdb.connect("localhost", self.username, self.password, "distcompdb")
        cursor = conn.cursor()
        fp = open("q_num_clients", "r")
        q = fp.read(1024)
        cursor.execute(q)
        s = cursor.fetchone()
        x = int(s[0])
        fp.close()
        conn.close()
        if x == 0:
            return False
        else:
            return True

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#Declaring global variable for multiple clients
Online_clients = []
Online_client_sockets = []
class Server: 

    def __init__(self):
        """Constructor for the server class """
        self.host = ''
        self.port = 5001
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []
        self.db = DBHandler()

    def open_socket(self):
        """Method to open a socket connection for listening to new client arrivals"""
        try: 
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            self.server.bind((self.host,self.port)) 
            self.server.listen(5) 
        except socket.error, (value,message): 
            if self.server: 
                self.server.close() 
            print "Could not open socket: " + message 
            sys.exit(1)

    def run(self):
        """ Method for running the server  """ 
        print "Opening socket..."
        self.open_socket() 
        print "Server socket opened ..."
        q = QueryClient(self.db)
        q.start()
        running = 1 
        #print "Listening for clients ..."
        while running:  
            #print "Listening for clients..."
            # handle the server socket
            c = Client(self.server.accept(), self.db) 
            c.start() 
            self.threads.append(c)

        # close all threads 
        self.server.close() 
        for c in self.threads: 
            c.join()  
            
#Class to handle queries to clients -----------------------------------------------------------------------------------------------------
class QueryClient(threading.Thread):
    """A single thread of this class runs..."""
    def __init__(self, dbase):
        threading.Thread.__init__(self)
        self.size = 1024
        self.db = dbase
    
    def run(self):
        print "Query client thread started and running ..."
        run = 1
        global Online_clients
        global Online_client_sockets
        while(run):
            time.sleep(5)
            i = 0
            if Online_clients == []:
                continue
            for client in Online_clients:
                client_id = client[0]
                client_ipaddr = client[1]
                x = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                x.connect((client_ipaddr, 5003))
                str = "FileQuery" #Query for getting the information of all articles in the client x
	        print "File query operation to client " + client_ipaddr
                x.send(str)
	        #Receive the input from the clients
                running = 1
                new_file_info = []
                while(running):
                    dt = x.recv(self.size)
                    info = dt.split(":")
                    if len(info) == 1:
                        break
                    elif len(info) == 4:
                        title = info[1]
                        author = info[3]
                        new_file_info.append((title,author))
                self.db.delete_tuples(client_id)
                for y in new_file_info:
                    t = y[0]
                    a = y[1]
                    self.db.insert_tuple(client_id, t, a)
                x.close()
	    time.sleep(30)
	    
	    
#Class to design thread for entertaining multiple clients -------------------------------------------------------------------------------
class Client(threading.Thread): 
    def __init__(self,(client,address),dbase): 
        threading.Thread.__init__(self) 
        self.client = client
        self.address = address 
        self.size = 1024 
        self.db = dbase

    def run(self):
        #Code for client log in
        print "Starting thread for client handling"
        login_id = self.client.recv(self.size)
        client_id = 0
        global Online_clients
        global Online_client_sockets
        if login_id == 'new':
            client_ipaddr = self.address[0]
            client_port = self.address[1]
            print "Registering new client with IP address: " + client_ipaddr + "and port: " + str(client_port)
            last_client = self.db.select_last_client()
            print "The last client is: " + str(last_client)
            next_client = last_client + 1
            self.db.insert_client_query(client_ipaddr, client_port)
            print "Sending client id as : " + str(next_client)
            data = str(next_client)
            self.client.send(data)
            client_entry = (next_client, client_ipaddr, client_port)
            client_id = next_client
            Online_clients.append(client_entry)
            Online_client_sockets.append(self.client)

            #TODO: Remove code below
            lc = self.db.select_last_client()
            print "The last client now is : " + str(lc)
        else:
            client_id = int(login_id)
            client_ipaddr = self.address[0]
            client_port = self.address[1]
            client_entry = (client_id, client_ipaddr, client_port)
            Online_clients.append(client_entry) 
            Online_client_sockets.append(self.client)
        print "Client has successfully logged in..."
        #Processing a logged in client
        running = 1 
        while running:
            data = self.client.recv(self.size)
            print "---------------------------------------------"
            print "Request received for the file: " + data 
            commands = data.split(":")
            print commands
            title = ""
            author = ""
            if len(commands) == 4:
                title = commands[1]
                author = commands[3]
            elif len(commands) == 2:
                if commands[0] == 'Title':
                    title = commands[1]
                    print "Title found: " + title
                else:
                    author = commands[1]
            elif len(commands) == 1 and commands[0] == 'stop':
                break
            
            #Process the queries
            yures = ""
            if (len(title) > 0) and (len(author) > 0):
                clients = []
                self.db.select_tit_auth_query(title,author,clients)
                #Check the list of online clients
                selected_clients = []
                for x in Online_clients:
                    if x[0] in clients:
                        selected_clients.append(x)
                yures = cPickle.dumps(selected_clients)
            elif (len(title) > 0):
                clients = []
                auth = []
                self.db.select_title_query(title, clients, auth)
                print clients
                print auth
                selected_clients = []
                indx = 0
                for x in clients:
		    for y in Online_clients:
		        if x == y[0]:
			    tup = (y[0], y[1], y[2], auth[indx])
			    selected_clients.append(tup)
			    break
	            indx += 1
	        yures = cPickle.dumps(selected_clients)
                print yures
	    elif(len(author) > 0):
	        clients = []
	        tit = []
	        self.db.select_author_query(author, clients, tit)
	        selected_clients = []
	        indx = 0
	        for x in clients:
		    for y in Online_clients:
		        if x == y[0]:
			    tup = (y[0], y[1], y[2], tit[indx])
			    selected_clients.append(tup)
			    break
		    indx += 1
                #print selected_clients
		yures = cPickle.dumps(selected_clients)
            self.client.send(yures)
        #Removing the client from the list of online clients
        for x in Online_clients:
	    if x[0] == client_id:
	        Online_clients.remove(x)
	Online_client_sockets.remove(self.client)
	self.client.close()
                    
if __name__ == "__main__": 
    s = Server() 
    s.run()  
