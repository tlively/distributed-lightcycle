from socket import SO_REUSEADDR, SOCK_STREAM, socket, SOL_SOCKET, AF_INET, gethostbyname, gethostname, SHUT_RDWR
from select import select
import player_pb2 as pb

# Some constants we'll be using later
BUFFERSIZE = 1024
HOST= gethostbyname(gethostname())
PORT = 2620
numplayers = 3

# Print so everyone else can run and connect
print("Started game setup! Other players connect now")
print("Host:{}".format(HOST))
print("Port: {}". format(PORT))

# Socket array for us to use later
player_sockets = {}

# Set up the socket for everyone to connect to
s = socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(numplayers - 1)

# Create our start message that we will add to and send along
start_msg = pb.StartMsg()
start_msg.proto_version = 1

# Accept everyone's connections
for i in range(numplayers-1):
	conn, addr = s.accept()
	conn.setblocking(0)
	player_sockets[str(i+2)] = conn
	# Set up the start message for this player and send
	start_msg.player_no = i + 2
	conn.send(start_msg.SerializeToString())
	# Update the rest of the info to add in this player
	player_ip = start_msg.players.add()
	player_ip.IP = addr[0]
	player_ip.player_no = i + 2
	player_sockets[str(i+2)] = conn
	
s.close()

msg = pb.PlayerIP()

while (1):
	for info in player_sockets.items():
		try:
			data = info[1].recv(BUFFERSIZE)
			if data:
				msg.ParseFromString(data)
				print(msg)
		except IOError:
			continue
