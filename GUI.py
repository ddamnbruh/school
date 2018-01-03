import socket
from _thread import start_new_thread
from tkinter import *
from tkinter import simpledialog
import base64

BUFF_RCV = 256

# label private message box

class project(Frame):
    def __init__(self, root):
        Frame.__init__(self, root)
        self.root = root
        self.initUI()
        self.allClients = {}
        self.counter = 0
        self.BUFF_RCV = 256
        self.soc = None
        self.username = ""
        self.key="CSC265isBesTclasS"
        self.clientList = []
        root.protocol('WM_DELETE_WINDOW', self.closeClient)

    def initUI(self):
        self.root.title('CrapChat')
        self.FrameSizeX = 800
        self.FrameSizeY = 600
        self.root.resizable(width=False, height=False)
        padX = 10
        padY = 10
        parentFrame = Frame(self.root)
        parentFrame.grid(padx=padX, pady=padY, stick=E + W + N + S)
        ipGroup = Frame(parentFrame)
        serverLabel = Label(ipGroup, text="Set: ")
        self.nameVar = StringVar()
        self.serverIPVar = StringVar()
        self.serverIPVar.set("localhost")
        serverIPField = Entry(ipGroup, width=15, textvariable=self.serverIPVar)
        serverIPField.bind("<Return>", self.connect)
        self.serverPortVar = StringVar()
        self.serverPortVar.set(3000)
        serverPortField = Entry(ipGroup, width=5, textvariable=self.serverPortVar)
        serverPortField.bind("<Return>", self.connect)
        self.serverSetButton = Button(ipGroup, text="Connect", width=10, command=self.connect, state=NORMAL)
        self.serverEndButton = Button(ipGroup, text='Disconnect', width= 10, command=self.closeConnect, state=DISABLED)
        serverLabel.grid(row=0, column=0)
        serverIPField.grid(row=0, column=2)
        serverPortField.grid(row=0, column=3)
        self.serverSetButton.grid(row=0, column=4, padx=5)
        self.serverEndButton.grid(row=0, column=5, padx=5)
        readMyChatGroup = Frame(parentFrame)
        yscrollbar = Scrollbar(readMyChatGroup)
        self.receivedChats = Text(readMyChatGroup, bg="white", width=60, height=20, state=DISABLED, yscrollcommand=yscrollbar.set)
        self.friendList = Text(readMyChatGroup, bg="white", width=30, height=10)
        self.private = Text(readMyChatGroup, bg="white", width = 30, height =10, state=DISABLED)
        self.receivedChats.grid(row=0, column=0, sticky=W + N + S)
        self.friendList.grid(row=0, column=2, sticky=E + N + S)
        self.private.grid(row=1, column=2, sticky=E + N + S)
        yscrollbar.grid(row=0, column=1, sticky=N+S, padx=(0, 10))
        writeMyChatGroup = Frame(parentFrame)
        self.chatVar = StringVar()
        self.chatField = Entry(writeMyChatGroup, bg="white", width=80, textvariable=self.chatVar)
        self.sendChatButton = Button(writeMyChatGroup, text="Send", width=10, command=self.handleSendChat, state=DISABLED)
        self.chatField.bind("<Return>", self.handleSendChat)
        self.chatField.grid(row=0, column=0, sticky=W)
        self.sendChatButton.grid(row=0, column=1, padx=5)
        self.statusLabel = Label(parentFrame)
        bottomLabel = Label(parentFrame, text="Michael Dylan Fernando")
        ipGroup.grid(row=0, column=0)
        readMyChatGroup.grid(row=1, column=0)
        writeMyChatGroup.grid(row=2, column=0, pady=10)
        self.statusLabel.grid(row=3, column=0)
        bottomLabel.grid(row=4, column=0, pady=10)

    def connect(self, event=None):
        username = self.username
        dialogText ='Enter a username:'
        while username == "" or len(username) > 10:
            username = simpledialog.askstring("Username", dialogText)
            if username is None:
                return
            elif username == "":
                dialogText = 'Enter a not blank username:'
            elif len(username) > 10:
                dialogText = 'Enter username less than 10 characters:'
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.soc.connect((str(self.serverIPVar.get()), int(self.serverPortVar.get())))
            self.initialization(self.soc, username)
            self.setStatus('Connected to remote host. Start sending messages')
            sys.stdout.flush()
            self.receivedChats.config(state=NORMAL)
            self.receivedChats.delete(1.0, END)
            self.receivedChats.config(state=DISABLED)
            self.serverSetButton.config(state=DISABLED)
            self.serverEndButton.config(state=NORMAL)
            start_new_thread(self.handleClientMessages, ())
        except socket.error:
            self.soc.close()
            return self.setStatus('Server not responding or wrong IP or port')
            

    def closeClient(self):
        if self.soc is None or self.soc.fileno() == -1:
            sys.exit(1)
        else:
            sys.stdout.flush()
            self.soc.send(self.encrypt("!close"))
            self.soc.close()
            self.setStatus("Disconnected from server")
            sys.exit(1)
            
    def closeConnect(self):
        sys.stdout.flush()
        self.soc.send(self.encrypt("!close"))
        self.soc.close()
        self.setStatus("Disconnected from server")
        self.serverEndButton.config(state=DISABLED)
        self.serverSetButton.config(state=NORMAL)
        self.sendChatButton.config(state=DISABLED)

    def handleClientMessages(self):
        self.sendChatButton.config(state=NORMAL)
        
        clientsoc = self.soc
        try:
            while 1:
                data = clientsoc.recv(BUFF_RCV)
                data = self.decrypt(data)
                print (data[0:7])
                if not data:
                    break
                elif data == "!lostConnect":
                    self.closeConnect()
                    break
                elif data[0:8] == '!Private':
                    data = data[8:]
                    self.addPrivate(data)
                else:
                    self.addChat(data)
                    if data[0:7] == '<Client':
                        username = data[7:]
                        username = username.split(' ')[1]
                        if 'connected' in data and 'not' not in data:
                            #self.updateFriends()
                            self.clientList.append(username)
                            self.updateFriends()
                        elif 'disconnected' in data:
                            for i in range(len(self.clientList)):
                                if self.clientList[i] == username:
                                    self.clientList[i].remove()
                                    self.updateFriends()
        except socket.error:
            clientsoc.close()
            
    def handleSendChat(self, event=None):
        clientsoc = self.soc
        msg = self.chatVar.get()
        if msg == '':
            return
        elif len(msg) > 256:
            self.setStatus("Message longer than 256 characters")
            self.chatVar.set("")
            return
        elif msg[0] == '/':
            self.addPrivate('me: ' + msg.split(' ', 1)[-1])
        else:
            self.addChat("me: " + msg)
        msg = self.encrypt(msg)
        clientsoc.send(msg)
        self.chatVar.set("")

    def addChat(self, msg):
        self.receivedChats.config(state=NORMAL)
        self.receivedChats.insert("end", msg + "\n")
        self.receivedChats.config(state=DISABLED)
        self.receivedChats.yview('end')

    def addPrivate(self, msg):
        self.private.config(state=NORMAL)
        self.private.insert("end", msg + "\n")
        self.private.config(state=DISABLED)
        self.private.yview('end')

    def updateFriends(self):
        self.friendList.config(state=NORMAL)
        self.friendList.delete(1.0, END)
        self.friendList.config(state=DISABLED)
        for i in range(len(self.clientList)):
            self.friendList.config(state=NORMAL)
            self.friendList.insert('end', self.clientList[i] + '\n')
            self.friendList.config(state=DISABLED)
            self.friendList.yview('end')

    def setStatus(self, msg):
        self.statusLabel.config(text=msg)
        print(msg)

    def initialization(self, client_socket, user_nickname):
        rcv_data = (client_socket.recv(BUFF_RCV))
        rcv_data = self.decrypt(rcv_data)
        if 'Hello version' not in rcv_data:
            sys.stdout.write('User connection is terminated, Server is not configured for this client!')
            sys.stdout.flush()
            client_socket.close()
            sys.exit(1)
        else:
            client_socket.send(self.encrypt('NICK ' + user_nickname))
            rcv_data = client_socket.recv(BUFF_RCV)
            rcv_data = self.decrypt(str(rcv_data))
            if 'ERROR' in rcv_data:
                sys.stdout.write(rcv_data + '\n')
                sys.stdout.flush()
                client_socket.close()
                sys.exit(1)
            else:
                return
            
    def encrypt(self, clear):
        enc = []
        for i in range(len(clear)):
            key_c = self.key[i % len(self.key)]
            enc_c = (ord(clear[i]) + ord(key_c)) % 256
            enc.append(enc_c)
        return base64.urlsafe_b64encode(bytes(enc))

    def decrypt(self, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc)
        for i in range(len(enc)):
            key_c = self.key[i % len(self.key)]
            dec_c = chr((256 + enc[i] - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)

def main():
    root = Tk()
    app = project(root)
    root.mainloop()

if __name__ == '__main__':
    main()