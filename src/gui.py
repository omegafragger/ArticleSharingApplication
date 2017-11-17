from Tkinter import *
import ttk
import time
import client
import sys
import threading
import tkMessageBox

class CreateGUI:
    def __init__(self):
        self.root = Tk()
        self.root.geometry("1000x800+500+500")
        self.label1 = None
        self.label2 = None
        self.label3 = None
        self.label4 = None
        self.label5 = None
        self.label6 = None
        self.label7 = None
        self.label8 = None
        self.titleEntry = None
        self.authorEntry = None
        self.searchArticleButton = None
        self.articleArea = None
        self.currentArticlesList = None
        self.searchResultsList = None
        self.saveButton = None
        self.progressBar = None
        self.haveflag = False

        #Objects for client framework handling
        self.userRequestHandler = client.UserFileRequestHandler()
        self.articleHandler = client.ArticleKeeper()
        self.artThread = None
        self.searchResults = []

    def createUI(self):
        self.label1 = Label(self.root, text="Search: ", relief=FLAT)
        self.label2 = Label(self.root, text="Title: ", relief=FLAT)
        self.label3 = Label(self.root, text="Author: ", relief=FLAT)
        self.titleEntry = Entry(self.root, bd = 3, width = 50)
        self.authorEntry = Entry(self.root, bd = 3, width = 30)
        #TODO: Must define action handler for this button
        self.searchArticleButton = Button(self.root, bd = 3, text="Search Article!!")
       
        #Next line
        self.label4 = Label(self.root, text="Article: ", relief=FLAT)
        self.label6 = Label(self.root, text="My Articles:", relief=FLAT)
        self.label7 = Label(self.root, text="Search Results:", relief=FLAT)
        self.articleArea = Text(self.root, bd = 3, height = 30, width = 50, state = DISABLED)
        self.currentArticlesList = Listbox(self.root, bd = 3, height = 30, width = 30, selectmode = SINGLE)
        self.searchResultsList = Listbox(self.root, bd = 3, height = 30, width = 42, selectmode = SINGLE)
        self.saveButton = Button(self.root, bd = 3, text="Save")

        self.label1.place(x = 15, y = 10)
        self.label2.place(x = 70, y = 10)
        self.titleEntry.place(x = 110, y = 10)
        self.label3.place(x = 530, y = 10)
        self.authorEntry.place(x = 590, y = 10)
        self.searchArticleButton.place(x = 860, y = 10)
        self.label4.place(x = 15, y = 35)
        self.articleArea.place(x = 15, y = 55)
        self.label6.place(x = 730, y = 35)
        self.currentArticlesList.place(x = 730, y = 55)
        self.label7.place(x = 380, y = 35)
        self.searchResultsList.place(x = 380, y = 55)
        self.saveButton.place(x = 180, y = 520)
        
        self.label8 = Label(self.root, text = "Progress: ", relief=FLAT)
        self.progressBar = ttk.Progressbar(self.root, orient="horizontal", length=900, mode="determinate")
        self.label8.place(x = 15, y = 560)
        self.progressBar.place(x = 80, y = 560)

        #Register event handlers
        self.searchArticleButton["command"] = self.searchArticleButtonHandler
        self.searchResultsList.bind('<<ListboxSelect>>', self.searchResultsListHandler)
        self.currentArticlesList.bind('<<ListboxSelect>>', self.currentArticlesListHandler)
        self.saveButton["command"] = self.saveButtonHandler
        self.saveButton["state"] = DISABLED

    def currentArticlesListHandler(self, event):
        """ Event handler for current articles list"""
        x = self.currentArticlesList.curselection()
        idx = int(x[0])
        strn = self.currentArticlesList.get(idx)
        info = strn.split("(")
        print info
        title = info[0][:-1]
        author = info[1][:-1]
        #print "currentArticlesListHandler method: title: "+title+" author: "+ author
        path = self.articleHandler.get_article(title, author)
        print path
        fp = open(path, "r+")
        strn = ""
        for l in fp:
            strn = strn + l
        fp.close()
        self.articleArea["state"] = NORMAL
        self.articleArea.delete('1.0', END)
        self.articleArea.insert(END, strn)
        self.articleArea["state"] = DISABLED
        self.saveButton["state"] = DISABLED

    def searchResultsListHandler(self, event):
        """Event handler for search Results list"""
        self.progressBar["value"] = 0
        x = self.searchResultsList.curselection()
        idx = int(x[0])
        ip = self.searchResults[idx][2]
        title = self.searchResults[idx][0]
        author = self.searchResults[idx][1]
        print "GUI Request: IP: " + str(ip) + "Title: " + str(title) + " Author: " + str(author)
        data = self.userRequestHandler.getFile(ip, title, author)
        print "We have the data..."
        self.articleArea["state"] = NORMAL
        self.articleArea.delete('1.0', END)
        self.articleArea.insert(END, data)
        self.articleArea["state"] = DISABLED
        self.saveButton["state"] = NORMAL
        self.haveflag = False

    def saveButtonHandler(self):
        """Event handler for the Save Button """
        self.articleArea["state"] = NORMAL
        text = self.articleArea.get("1.0", END)
        text = text[:-1]
        lines = text.split("\n")
        title = lines[0]
        author = lines[1]
        filename = lines[0]
        self.articleArea["state"] = DISABLED
        path = self.articleHandler.getfirstsearchpath()
        fle = path+filename
        fp = open(fle, "w")
        fp.write(text)
        fp.close()
        self.start_download()
        self.currentArticlesList.insert(END, title+ " ("+author+")")
        
    def searchArticleButtonHandler(self):
        """Event handler for search Articles Button """
        self.progressBar["value"] = 0
        self.saveButton["state"] = DISABLED
        titleSearch = self.titleEntry.get()
        authorSearch = self.authorEntry.get()
        self.searchResults = []
        if titleSearch == "" and authorSearch == "":
            tkMessageBox.showinfo("ArticleShare Inc.", "Enter either title or author or both")
            return
        elif titleSearch != "" and authorSearch == "":
            res = self.userRequestHandler.getArticle(title = titleSearch)
            ipaddrs = []
            for x in res:
                ip = x[1]
                ipaddrs.append(ip)
            delays = self.userRequestHandler.getPeerDelays(ipaddrs)
            i = 0
            for x in res:
                tit = titleSearch
                auth = x[3]
                ipad = ipaddrs[i]
                delay = delays[i]
                self.searchResults.append((tit, auth, ipad, delay))
                i += 1
        elif titleSearch == "" and authorSearch != "":
            res = self.userRequestHandler.getArticle(author = authorSearch)
            ipaddrs = []
            for x in res:
                ip = x[1]
                ipaddrs.append(ip)
            delays = self.userRequestHandler.getPeerDelays(ipaddrs)
            i = 0
            for x in res:
                tit = x[3]
                auth = authorSearch
                ipad = ipaddrs[i]
                delay = delays[i]
                self.searchResults.append((tit, auth, ipad, delay))
                i += 1
        elif titleSearch != "" and authorSearch != "":
            res = self.userRequestHandler.getArticle(titleSearch, authorSearch)
            ipaddrs = []
            for x in res:
                ip = x[1]
                ipaddrs.append(ip)
            delays = self.userRequestHandler.getPeerDelays(ipaddrs)
            i = 0
            for x in res:
                tit = titleSearch
                auth = authorSearch
                ipad = ipaddrs[i]
                delay = delays[i]
                self.searchResults.append((tit, auth, ipad, delay))
                i += 1
        #Print the search results as a list
        self.searchResultsList.delete(0,END)
        print "Printing search results: "
        for x in self.searchResults:
            print x
            strn = str(x[0]) + " (" + str(x[1]) + ", " + str(x[3][1]) + " ms)"
            self.searchResultsList.insert(END, strn)
    

    #Functions for progress bar animation
    def start_download(self):
        self.progressBar["value"] = 0
        self.progressBar["maximum"] = 50000
        x = 0
        while x <= 50000:
            self.progressBar["value"] = x
            self.progressBar.update()
            x += 500
            time.sleep(0.05)

    def activateUI(self):
        self.artThread = ArticleThread(self.currentArticlesList, self.articleHandler)
        self.artThread.start()
        self.root.mainloop()

#--------------------------------------------------------------------------------------------------------------------
#Class for running a thread for maintaining the list of current articles
class ArticleThread(threading.Thread):
    """A class for maintaining and updating the current list of articles present in the client"""
    def __init__(self, currentArticles, articleHandler):
        threading.Thread.__init__(self)
        self.currentArticlesList = currentArticles
        self.articleh = articleHandler

    def run(self):
        run = 1
        while(run):
            titles = []
            authors = []
            self.articleh.list_articles(titles,authors)
            sz = self.currentArticlesList.size()
            self.currentArticlesList.delete(0,END)
            i = 0
            for x in titles:
                auth = authors[i]
                self.currentArticlesList.insert(END, x+" ("+auth+")")
                i += 1
            time.sleep(10)

#-------------------------------------------------------------------------------------------------------------
if __name__=="__main__":
    if (len(sys.argv) != 2):
        print "Invalid number of arguments!"
        sys.exit()
    ipaddr = sys.argv[1]
    #Starting the thread for serving clients
    serveOtherClients = client.ServeClient()
    serveOtherClients.start()
    #Starting the thread for server communication
    talkServer = client.ContactServer(ipaddr)
    talkServer.start()

    gui = CreateGUI()
    gui.createUI()
    gui.activateUI()

