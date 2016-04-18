import sys
import time
from socket import SO_REUSEADDR, SOCK_STREAM, error, socket, SOL_SOCKET, AF_INET, SHUT_RDWR, gethostbyname, gethostname
import player_pb2 as pb

BUFFERSIZE = 1024

player_sockets = {}
numplayers = 3

# Ensure proper usage
def usage_error():
	print("Usage: python main.py [IP] [port]")
	sys.exit()

if (len(sys.argv) != 3):
        usage_error()

try:
    PORT = int(sys.argv[2])
except:
    print("Invalid port number")
    usage_error()
HOST = sys.argv[1]

# Set up the socket and connect to player 1
s1 = socket(AF_INET, SOCK_STREAM)
s1.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s1.connect((HOST, PORT))

player_sockets['1'] = s1

# get the rest of the players from over the network
players = s1.recv(BUFFERSIZE)
s1.setblocking(0)

player_data = pb.StartMsg()
player_data.ParseFromString(players)

me = player_data.player_no

print(player_data)

s = socket(AF_INET, SOCK_STREAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
s.bind((gethostbyname(gethostname()), PORT + me))
s.listen(numplayers-me)

for i in range(me, numplayers):
	conn, addr = s.accept()
	conn.setblocking(0)
	player_sockets[str(i+1)] = conn

s.close()

for player in player_data.players:
	s = socket(AF_INET, SOCK_STREAM)
	s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	s.connect((player.IP, PORT + player.player_no))
	s.setblocking(0)
	player_sockets[str(player.player_no)] = s

myinfo = pb.PlayerIP()
myinfo.player_no = me
myinfo.IP = gethostbyname(gethostname())
confirmMsg = myinfo.SerializeToString()

for info in player_sockets.items():
	info[1].send(confirmMsg)

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

print(player_data)
