import sys, random, struct
import socket as sock
import player_pb2 as pb
from game_utils import Message, Direction

N_PLAYERS = 4
PORT = 2620
LOCAL_ADDR = sock.gethostbyname(sock.gethostname())

class SelfLoopSocket(object):
    def __init__(self):
        self.msgs = ''

    def send(self, msg):
        self.msgs += msg

    def recv(self, buf_len):
        if buf_len < len(self.msgs):
            buf = self.msgs[:buf_len]
            self.msgs = self.msgs[buf_len:]
            return buf
        else:
            buf = self.msgs
            self.msgs = ''
            return buf

class WrappedSocket(object):
    """
    Like a socket, but reads always return an individual message (or nothing)
    """
    def __init__(self, socket, failprob=0):
        self.socket = socket
        self.failprob = failprob

    def send(self, msg):
        if random.random() > self.failprob:
            self.socket.send(struct.pack("!Q", len(msg)) + msg)

    def recv(self, buf_len):
        data = self.socket.recv(8)
        if not data: return
        assert len(data) == 8
        msglen = struct.unpack("!Q", data)[0]
        data = self.socket.recv(msglen)
        assert len(data) == msglen
        return data

def establish_tcp_connections(host_ip):
    """
    Connect to `host_ip' and establish the fully connected network
    of four players.
    Args: host_ip - the address of the game coordinator, or None if
        the local player is the game coordinator.
    Returns: a tuple of the local player's number, a list of four
        nonblocking sockets connected to each player, and a list of
        the four player addresses.
    """
    local_player = 0
    player_socks = [None] * N_PLAYERS
    player_addrs = [host_ip] + [None] * (N_PLAYERS - 1)

    # connect to coordinator (player 0)
    host_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    host_sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    host_sock.connect((host_ip, PORT))

    # receive a player number and other addresses
    msg = pb.StartMsg()
    msg_str = host_sock.recv(1024)
    msg.ParseFromString(msg_str)
    local_player = msg.player_no
    other_players = [(player.player_no, player.IP) for player in msg.players]

    # record addresses
    player_addrs[0] = host_ip
    for p, addr in other_players:
        player_addrs[p] = addr

    # check that we received the proper amount of information
    assert len(other_players) == local_player - 1

    # prep the host socket for return
    host_sock.setblocking(0)
    player_socks[0] = host_sock

    # listen for connections from other players
    listener = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    listener.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    listener.bind((LOCAL_ADDR, PORT + local_player))
    listener.listen(N_PLAYERS - local_player)

    # process incoming connections
    for p in range(local_player + 1, N_PLAYERS):
        conn, addr = listener.accept()
        msg_str = conn.recv(1024)
        msg = pb.PlayerIP()
        msg.ParseFromString(msg_str)

        # add to list of connections
        conn.setblocking(0)
        player_socks[msg.player_no] = conn
        player_addrs[msg.player_no] = addr[0]

    listener.close()

    # connect to other players
    for p in range(1, local_player):
        p_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        p_sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
        p_sock.connect((player_addrs[p], PORT + p))

        # send our player number for identification
        msg = pb.PlayerIP()
        msg.player_no = local_player
        msg.IP = LOCAL_ADDR
        p_sock.send(msg.SerializeToString())

        # record sock
        p_sock.setblocking(0)
        player_socks[p] = p_sock

    # create self loop
    player_addrs[local_player] = LOCAL_ADDR
    player_socks[local_player] = SelfLoopSocket()

    player_socks = map(WrappedSocket, player_socks)

    return (local_player, player_socks, player_addrs)

def coordinate_tcp_connections():
    """
    Coordinate the creation of the fully connected network of four
    players, assigning player numbers by connection order.
    Returns: a tuple of the local player's number, a list of four
        nonblocking sockets connected to each player, and a list of
        the four player addresses.
    """
    print 'hosting at', LOCAL_ADDR

    player_socks = [None] * N_PLAYERS
    player_addrs = [None] * N_PLAYERS
    # Set up the socket for everyone to connect to
    listener = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    listener.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    listener.bind((LOCAL_ADDR, PORT))
    listener.listen(N_PLAYERS)

    # Create our start message that we will add to and send along
    start_msg = pb.StartMsg()
    start_msg.proto_version = 1

    # Accept everyone's connections
    for i in range(1, N_PLAYERS):
        conn, addr = listener.accept()
        conn.setblocking(0)
        # Set up the start message for this player and send
        start_msg.player_no = i
        conn.send(start_msg.SerializeToString())
        # Update the rest of the info to add in this player
        player_ip = start_msg.players.add()
        player_ip.IP = addr[0]
        player_ip.player_no = i
        player_socks[i] = conn
        player_addrs[i] = addr

    listener.close()

    # create self loop
    player_addrs[0] = LOCAL_ADDR
    player_socks[0] = SelfLoopSocket()

    player_socks = map(WrappedSocket, player_socks)

    return (0, player_socks, player_addrs)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # conect to given host
        establish_tcp_connections(sys.argv[1])
    else:
        coordinate_tcp_connections()
