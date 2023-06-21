import socket
import threading
import sqlite3
import os
import pickle
import Question as Question
from datetime import datetime, timedelta, time

HOST = "127.0.0.1"
PORT = 5555
FORMAT = "utf-8"
SIZE = 1024
#ThreadCount = 0
time = datetime.now()
serverTime = time.strftime("%H:%M:%S")
#Used in the broadcast
clients = []
loginNames = []
#name of the directory where files will be stored
serverFilePath = "host_files"
last_save_time = time.time()
#connecting/creating db
dbconnection = sqlite3.connect('clients.db',check_same_thread=False)
db = dbconnection.cursor()
db.execute("""CREATE TABLE IF NOT EXISTS clientes (
                login text PRIMARY KEY,
                presenca integer,
                atrasado integer,
                falta integer
)""")
           
class MassageBuilder:
    def __init__(self,message):
        self.string = message

    def add(self, message):
        self.string = self.string+message
    
    def __str__(self):
        return f"{self.string}"


def saveQuestions(questions, file_name):
    with open(file_name, "wb") as file:
        pickle.dump(questions, file)

def loadQuestions(file_name):
    with open(file_name, "rb") as file:
        questions = pickle.load(file)
    return questions

if os.path.exists("saveFile"):
    questions = loadQuestions("saveFile")
else:
    questions = []

def broadcast(message):
    for client in clients:
        client.send(message.encode(FORMAT))

def ClientLogin(login):
    #Query to see if its a new client or existing one
    ClientTime = datetime.now()
    db.execute(f"SELECT EXISTS(SELECT 1 from clientes WHERE login ='{login}')")
    for y in db.fetchall():
            for z in y:
                #in case user dosent exists in db, he is added
                if z == 0:
                    db.execute(f"INSERT INTO clientes VALUES ('{login}',?,?,?)",(0,0,0,))
                    dbconnection.commit()
    #Depending on the time when the client logins, he gets a level of attendance added
    if ClientTime <= time+timedelta(minutes=20):
        db.execute(f"UPDATE clientes SET presenca = presenca+1 WHERE login = '{login}'")
        # db.execute(f"SELECT * FROM clientes where login = '{login}'")
        # rows = db.fetchall()
        # print(rows)
        dbconnection.commit()
    elif ClientTime > time+timedelta(minutes=20) and ClientTime <= time+timedelta(minutes=45):
        db.execute(f"UPDATE clientes SET atrasado = atrasado+1 WHERE login = '{login}'")
        dbconnection.commit()
    elif ClientTime > time+timedelta(minutes=45):
        db.execute(f"UPDATE clientes SET falta = falta+1 WHERE login = '{login}'")
        dbconnection.commit()  


#Function to take care of the message of the clients and calling the necessary functions for each case
def handle_client(connection, addr):
    print(f"[NEW CONNECTION] {addr}\n")
    loginNames.append(addr) #use the addr as a temporary alias
    connected = True
    while connected:
        #try:    
            received = connection.recv(SIZE).decode(FORMAT)
            #EXIT is used as a way to logout as a client
            if received == "EXIT":
                index = clients.index(connection)
                connected = False
                print(f"[{loginNames[index]}]: has left the chat")
                send = "bye"
            else:
                index = clients.index(connection)
                print(f"({loginNames[index]})  {received}")
                send = "received message :D"
            command = received.split(' ', 1)
            if command[0] == "ASK" or "AWNSER"or"LISTQUESTIONS"or"IAM"or"PUTFILE" or "LISTFILES" or "GETFILE":
                #In case of someone posting a question
                if command[0] == "ASK":
                    asked=Question.Question(len(questions)+1, command[1])
                    send = "QUESTION "+asked.toString()
                    questions.append(asked)                         #adding the quest in the list of questions
                    #connection.send(send.encode(FORMAT))
                    saveQuestions(questions,"saveFile")
                    broadcast(send)

                #when someone wants to awnser a posted question
                elif command[0] == "AWNSER":
                    index = clients.index(connection)
                    awnser=command[1].split(' ', 1)
                    numQuestion = int(str(awnser[0]))
                    awnQuestion = awnser[1]
                    questions[numQuestion-1].setAwnser(f"({loginNames[index]}) " + f"{awnQuestion}")
                    sand = f"REGISTERED {numQuestion}"
                    saveQuestions(questions,"saveFile")
                    connection.send(sand.encode(FORMAT))

                #Case where all questions and the awnser to each os them is listed
                elif command[0] == "LISTQUESTIONS":
                    # contador = 0
                    # while contador < len(questions):
                    msg = MassageBuilder("")
                    for x in questions:
                        msg.add("QUESTION "+x.toString()+"\n")
                        temp = x.getAwnser()
                        for y in temp:
                            msg.add(y+"\n")
                    print(msg)
                    msg.add("ENDQUESTIONS")
                    broadcast(str(msg))
                #In case of a new login in the database
                elif command[0] == "IAM":
                    login = command[1]
                    ClientLogin(login)
                    loginNames.remove(addr)
                    loginNames.append(login)
                    send = f"HELLO {login}"
                    connection.send(send.encode(FORMAT))
            #Now for the third part of the file managment
                # Now for the third part of the file management
                elif command[0] == "PUTFILE":
                    base = received.split(' ')
                    fileName = base[1]
                    fileSize = int(base[2])
                    filePath = os.path.join(serverFilePath, fileName)
                    received_data = 0
                    with open(filePath, 'wb') as file:
                        while received_data < fileSize:
                            data = connection.recv(SIZE)
                            received_data += len(data)
                            file.write(data)
                    send = f"UPLOADED {fileName}"
                    connection.send(send.encode(FORMAT))
                #if is requested a list of all files the server currently have
                elif received == "LISTFILES":
                    files = os.listdir(serverFilePath)
                    if len(files) == 0:
                        send = "No files available"
                        connection.send(send.encode(FORMAT))
                    else:
                        msg = MassageBuilder('')
                        counter = 0
                        for title in files:
                            counter += 1
                            msg.add(f"({counter}) "+title+"\n")
                        msg.add("ENDFILES\n")
                        connection.send(str(msg).encode(FORMAT))
                elif command[0] == "GETFILE":
                    fileNumber = int(str(command[1]))
                    files = os.listdir(serverFilePath)
                    msg = MassageBuilder('FILE ')
                    counter = 1
                    for title in files:#verify if the file exists
                        counter +=1
                        if counter == fileNumber:#If exists what is the position
                            fileSize = os.path.getsize(title)#get their size
                            msg.add(f"{counter} {title} {fileSize}")
                        connection.send(str(msg).encode(FORMAT))#send the main message
                        filePath = os.path.join(serverFilePath, fileName)
                        with open(os.path.join(serverFilePath,title), 'rb') as file:
                            while True:
                                data = file.read(fileSize)
                                if not data:
                                    break
                                connection.send(data)#followed by the rest of the file
                #in case of a not implemented input
                else:
                    send = "wrong input"
                    connection.send(send.encode(FORMAT))                
        # except:
        #     error = clients.index(connection)
        #     exClient = loginNames[error]
        #     print(f"client {exClient} had an error, closing connection")
        #     loginNames.remove(exClient)
        #     clients.remove(connection)
        #     connection.close()

def main():
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.bind((HOST, PORT))
    except socket.error as e:
        print(str(e))

    s.listen()
    print(f"Listening on {HOST} : {PORT}")
    while True:
        connection, addr = s.accept()
        clients.append(connection)
        thread = threading.Thread(target = handle_client, args = (connection, addr))
        thread.start()
        # print(f"ACTIVE CONNECTIONS {threading.activeCount() -1}") used to test if was gettin multiple clients

if __name__ == "__main__":
    main()