import socket
import threading

HOST = "127.0.0.1"
PORT = 5555
FORMAT = "utf-8"
SIZE = 1024
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((HOST,PORT))

#the reason this is divded in functions is just so they can start in each thread separadtly
def recive():
    connected = True
    while connected:
        message = client.recv(SIZE).decode(FORMAT)
        print(message)
        if message == "bye":
                connected = False
    client.close()
 
def send():
    connected = True
    while connected:
        msg = input("-> ")
        isUpload = msg.split(' ')
        client.send(msg.encode(FORMAT))
        if isUpload[0] == "PUTFILE":
            file = open(isUpload[1],'rb')
            fileData = file.read(int(str(isUpload[2])))
            client.sendall(fileData)
            file.close()
        elif msg == "EXIT":
            connected = False
    client.close()
    
def main():
    reciveThread = threading.Thread(target=recive)
    reciveThread.start()

    sendThread = threading.Thread(target=send)
    sendThread.start()

if __name__ == "__main__":
    main()