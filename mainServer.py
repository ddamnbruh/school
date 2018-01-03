import socket
import select
import sys
import base64

def initialization(transmitting_socket):

    hello = encrypt('Hello version')
    transmitting_socket.send(hello)
    data_to_send = decrypt(transmitting_socket.recv(512))

    if 'NICK' not in data_to_send:
        transmitting_socket.send(encrypt('ERROR : NICK was not included please check again'))
        return
    else:
        nickname_prefix, client_nickname = data_to_send.split(' ', 1)
        transmitting_socket.send(encrypt('OK'))
    return client_nickname


# Function to broadcast chat messages to all connected clients
def broadcast_data(transmitting_sock, message):
    # Do not send the message to master socket and the client who has send us the message
    for know_socket in CONNECTION_LIST:
        if know_socket != server_socket and know_socket != transmitting_sock:
            know_socket.send(encrypt(message))

def serverQuit():
    broadcast_data(sock, "!lostConnect")
    
def encrypt(clear):
    key="CSC265isBesTclasS"
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = (ord(clear[i]) + ord(key_c)) % 256
        enc.append(enc_c)
    return base64.urlsafe_b64encode(bytes(enc))

def decrypt(enc):
    key="CSC265isBesTclasS"
    dec = []
    enc = base64.urlsafe_b64decode(enc)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + enc[i] - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

if __name__ == "__main__":
    BUFFER_RCV = 512
    MAX_BUFFER_RCV = 255

    host="localhost"
    port=3000
    
    #host = '10.128.0.2'
    #port = 80

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this has no effect, why ?
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)

    # List to keep track of socket descriptors
    CONNECTION_LIST = list([])
    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    print ("Chat server started on port " + str(port))

    # Initialization to bind the port with the name
    dictionary = {}
    userNameList = []

    while 1:
        # Get the list sockets which are ready to be read through select
        read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST,
                                                                   [],
                                                                   [])

        for sock in read_sockets:
            # New connection
            if sock == server_socket:
                # Handle the case in which there is a new connection received through server_socket
                socket_fd, address = server_socket.accept()
                CONNECTION_LIST.append(socket_fd)
                newUserNickname = initialization(socket_fd)
                dictionary[address[1]] = newUserNickname
                userNameList.append(newUserNickname)
                print ("<Client " + newUserNickname + " connected>")
                broadcast_data(sock, "<Client " + newUserNickname + " connected>")
            # Some incoming message from a client
            else:
                # Data received from client, process it
                data = sock.recv(BUFFER_RCV)
                data = decrypt(data)
                broadcastingHost, broadcastingSocket = sock.getpeername()
                if '!close' in data:
                    # Closing bind port client with server due to client
                    # request. Removing socket from list in future broadcast
                    broadcast_data(sock, "<Client " + dictionary[broadcastingSocket] + " has left the room>")
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    #userNameList.remove()
                    print("<Client " + dictionary[broadcastingSocket] + " has left the room>")
                    del dictionary[broadcastingSocket]
                    
                elif data[0] == "/":
                    username = data[1:].split(' ', 1)[0]
                    data = data.split(' ', 1)[-1]
                    print(dictionary[broadcastingSocket])
                    if username in userNameList:
                        for x in range(len(userNameList)):
                            if userNameList[x] == username:
                                CONNECTION_LIST[x+1].send(encrypt('!Private' + dictionary[broadcastingSocket] + ': ' + data))
                                print('<Private message from ' + dictionary[broadcastingSocket] + ': ' + data + '>')
                    else:
                        sock.send(encrypt("<Client " + username + " is not connected>"))
                                         
                else:
                    broadcast_data(sock, "\r" + dictionary[broadcastingSocket]+ ": " + data)
    server_socket.close()
    sys.exit(0)