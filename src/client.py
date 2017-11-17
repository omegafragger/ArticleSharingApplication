import os
import select
import socket
import sys
import threading
import dbauthorization
import time
import cPickle

#------------------------------------------------------------------------------------------------------------------------------------
class ArticleKeeper:
    """A class used to search and modify the searchpaths for article searching and checking existing articles and their authors"""
    
    def clear_paths(self):
        with open("searchpaths", "w"):
            pass

    def create_searchpaths(self, sp_list):
        """A method to refresh the search paths with the list of search paths given in sp_list"""
        clear_paths()
        fp = open("searchpaths", "w+")
        for x in sp_list:
            fp.write(x+"\n")
        fp.close()

    def getfirstsearchpath(self):
        """ A method to get the first search path in the list of search paths """
        fp = open("searchpaths", "r+")
        for x in fp:
            ln = x[:-1]
            return ln

    def list_articles(self, titles, authors):
        """ A method to extract the articles from the search paths and their respective titles and authors"""
        fp = open("searchpaths", "r+")
        for path in fp:
            path = path[:-1]
            files = os.listdir(path)
            for fle in files:
                if fle[-1] == '~':
                    continue
                else:
                    fpt = open(path+fle, "r+")
                    title = ""
                    author = ""
                    cnt = 1
                    for ln in fpt:
                        if cnt == 1:
                            title = ln[:-1]
                            cnt = cnt + 1
                        elif cnt == 2:
                            author = ln[:-1]
                            cnt = cnt + 1
                        else:
                            break
                    titles.append(title)
                    authors.append(author)

    def get_article(self, title, author):
        """A method to output the path of the article given its title and author"""
        fp = open("searchpaths", "r+")
        for path in fp:
            path = path[:-1]
            files = os.listdir(path)
            for fle in files:
                if (fle[-1] != '~'):
                    fpt = open(path+fle, "r+")
                    tit = ""
                    auth = ""
                    cnt = 1
                    for ln in fpt:
                        if cnt == 1:
                            tit = ln[:-1]
                            cnt += 1
                        elif cnt == 2:
                            auth = ln[:-1]
                            cnt += 1
                        else:
                            break
                    if (tit == title) and (auth == author):
                        res = path+fle
                        fpt.close()
                        return res

#------------------------------------------------------------------------------------------------------------------------------------
#The Server part of the Client code
class ServeClient(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = ""
        self.port = 5002
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []
        
    def open_socket(self):
        """A method to open new sockets for incoming clients"""
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
        self.open_socket() 
        running = 1 
        while running: 
            c = ClClient(self.server.accept()) 
            c.start() 
            self.threads.append(c) 

        # close all threads 

        self.server.close() 
        for c in self.threads: 
            c.join()

#Class for handling peer requests to receive a file --------------------------------------------------------------------------------
class ClClient(threading.Thread):
    def __init__(self, (client, address)):
        threading.Thread.__init__(self)
        self.client = client
        self.address = address
        self.ak = ArticleKeeper()
        self.size = 1024

    def run(self):
        running = 1
        while(running):
            command = self.client.recv(self.size)
            if command != 'GetFile' and command != 'Stop' and command != 'Ping':
                #Command not found
                continue
            elif command == 'Stop':
                break
            elif command == 'Ping':
                self.client.send('Ping')
                continue
            self.client.send("Okay")
            print "GetFile request received..."
            info = self.client.recv(self.size)
            commands = info.split(":")
            title = commands[1]
            author = commands[3]
            path = self.ak.get_article(title, author)
            fpt = open(path, "r+")
            for line in fpt:
                self.client.send(line)
                resp = self.client.recv(self.size)
            fpt.close()
            self.client.send("EOF")
            print "GetFile request responded to ..."
#----------------------------------------------------------------------------------------------------------------------------------
Client_Request = ""#Global variable to be filled when the client requests for an article
Answers = [] #Global variable to store the results obtained from the server
#----------------------------------------------------------------------------------------------------------------------------------
#Code for connecting over to the database server and also serve client queries
class ContactServer(threading.Thread):
    def __init__(self, ipaddr):
        threading.Thread.__init__(self)
        self.size = 1024
        self.serverport = 5001 #Port on which server is running, ipaddr gives the IP address of the server
        self.serverip = ipaddr
        self.client_sock = None
        self.serverQueryHandler = None

    def connectToServer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.serverip, self.serverport))
        return sock

    def run(self):
        global Client_Request
        global Answers
        self.client_sock = self.connectToServer()
        #Code for logging into the server
        self.client_id = ""
        fp = open("client_noteid", "r+")
        for line in fp:
            #line = line[:-1]
            self.client_sock.send(line)
            if line == "new":
                self.client_id = self.client_sock.recv(self.size)
                print "client id received: " + self.client_id
            else:
                self.client_id = line
        fp.close()
        """with open("client_noteid", "w"):
            pass"""
        fp = open("client_noteid", "w")
        print "Writing the client id in file as: " + self.client_id
        fp.write(str(self.client_id))
        fp.close()
        #End of code for client login
        
        #Starting separate thread for handling server side requests        
        self.serverQueryHandler = ServerQueryHandler(self.client_sock)
        self.serverQueryHandler.start()
        
        run = 1
        while(run):
            if Client_Request == "":
                continue
            else:
                print " ------------------------------------------------------------"
                print "Client Request : " + Client_Request
                self.client_sock.send(Client_Request)
                res = self.client_sock.recv(self.size)
                print "Response received: " + res
                Answers = cPickle.loads(res)
                print Answers
                print " ------------------------------------------------------------"
                Client_Request = ""
#------------------------------------------------------------------------------------------------------------------------------
class ServerQueryHandler(threading.Thread):
    """Class for handling client side server request handling """
    def __init__(self, client_sock):
        threading.Thread.__init__(self)
        self.size = 1024
        self.sock = client_sock
        self.host = ""
        self.port = 5003
        self.article_handler = ArticleKeeper()

    def run(self):
        print "Server request handler thread running..."
        running = 1
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host,self.port))
        self.sock.listen(5)
        print "Listening for server requests..."
        while(running):
            obj = HandleServerQueries(self.sock.accept(), self.article_handler)
            obj.start()
            obj.join()
        self.sock.close()
#------------------------------------------------------------------------------------------------------------------------------
class HandleServerQueries(threading.Thread):
    def __init__(self, (sock,addr), articleHandler):
        threading.Thread.__init__(self)
        self.sock = sock
        self.size = 1024
        self.articleHandler = articleHandler

    def run(self):
        server_request = self.sock.recv(self.size)
        #print "Server request encountered..."
        if server_request == "FileQuery":
            titles = []
            authors = []
            self.articleHandler.list_articles(titles, authors)
            i = 0
            for title in titles:
                author = authors[i]
                str = "Title:"+title+":Author:"+author
                i+=1
                #print "Sending: " + str
                self.sock.send(str)
                time.sleep(1)
            #print "Sending: Stop"
            self.sock.send("Stop")
#------------------------------------------------------------------------------------------------------------------------------
#End of code for connecting with server on a separate thread
class UserFileRequestHandler:
    """A class which handles event based function calling for getting a file from another peer client"""
    def __init__(self):
        self.size = 1024
        self.sock = None
        self.port = 5002 #Port on which peer is running

    def getArticle(self, title = "", author = ""):
        """A method to handle the three possible cases for a user request
           Case 1: Both a title and an author is provided
           Case 2: Only a title and no author
           Case 3: Only an author and no tilte """
        global Client_Request
        global Answers
        if title != "" and author != "":
            request = "Title:"+title+":Author:"+author
            Client_Request = request
        elif title != "" and author == "":
            print "Global variable Client_Request set from getArticle method..."
            request = "Title:"+title
            Client_Request = request
        elif title == "" and author != "":
            request = "Author:"+author
            Client_Request = request
        #Wait for some time
        time.sleep(2)
        #Code for accessing the response from the server through Answers
        while(True):
            if Answers != []:
                res = list(Answers)
                return res
                Answers = []
    
    def getPeerDelays(self, ipaddrs):
        """A method to test the peer delay of each online peer"""
        peer_delays = []
        sock = None
        for x in ipaddrs:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((x,self.port))
            start_time = time.time()
            sock.send("Ping")
            repl = sock.recv(self.size)
            if repl == "Ping":
                end_time = time.time()
                delay = end_time - start_time
                delay = round((delay * 1000),2)
                tup = (x, delay)
                peer_delays.append(tup)
            sock.send("Stop")
            sock.close()
        return peer_delays
 
    def getFile(self, ipaddr, title = "", author = ""):
        """A method to connect to a peer and either read or get a file"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ipaddr,self.port))
        print "getFile Method: Socket connection established"
        #Sending request for a file
        self.sock.send("GetFile")
        resp = self.sock.recv(self.size)
        if resp != "Okay":
            return
        data = "Title:"+title+":Author:"+author
        self.sock.send(data)
        print "getFile Method: Socket request sent"
        run = 1
        strn = ""
        while(run):
            temp = self.sock.recv(self.size)
            self.sock.send("Okay")
            if temp != "EOF":
                strn = strn + temp
            else:
                break
        print "getFile Method: Response received"
        print strn
        self.sock.send("Stop")
        self.sock.close()
        return strn
