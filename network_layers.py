import time, random
from socket import *
from select import select
import player_pb2 as pb

from game_utils import GameState, Direction, Message

# handles setting up and using the network interfacing
from network_utils import *

class NetworkLayer(object):
    """
    Responsible for handling networking operations. Provides an
    interface for communicating with other players in the game. Must
    be subclassed to be used.
    """

    def broadcast_message(self, msg):
        """
        Broadcast a message to other players.
        Args:
            msg: the message to broadcast
        Return:
            True if the message was successfully broadcast,
            False otherwise.
        """
        return False

    def get_messages(self):
        """
        Get queued incoming messages. Does not block to wait for
        messages.
        Return:
            An Iterable of Messages
        """
        return []

    def wait_for_ready(self):
        """
        Block until the game is supposed to begin.
        """
        while True:
            pass

class RandomNoNetworkLayer(NetworkLayer):
    """
    A NetworkLayer implementation meant for user interface testing. It
    does not actually do any network requests and it will generate
    random moves for all players.
    """

    def __init__(self, player, game):
        self.player = player
        self.game = game
        self.message_queue = []
    
    def broadcast_message(self, msg):
        """Pretend to broadcast the message."""
        self.message_queue.append(msg)
        return True

    def get_messages(self):
        """
        Yield the start messages and then yield a random message with
        probability .05
        """
        while True:
            if len(self.message_queue) > 0:
                yield self.message_queue.pop(0)
                continue
            if random.random() < .95:
                raise StopIteration
            else:
                possible_players = [p for p in self.game.players_left
                                    if p != self.player]
                if len(possible_players) == 0:
                    raise StopIteration
                p = possible_players[0]
                if len(possible_players) > 1:
                    p = possible_players[random.randint(0,len(possible_players)-1)]
                new_dir = Direction(random.randint(0,2))
                new_t = time.time()
                new_pos = self.game.state[p][-1]['pos']
                yield Message.move(p, new_pos, new_dir)

    def start(self):
        """Start the game immediately"""
        pass

class NaiveNetworkLayer(NetworkLayer):
    """
    A NetworkLayer implementation that uses simple message passing with
    no aggreement algorithm for game state. Should show liveness but might
    show inconsistencies.
    """

    def __init__(self, game, HOST=None):
        self.game = game
        self.message_queue = []
        self.HOST = HOST
        # These get initialized in start
        self.player = None
        self.socks = None
        self.addrs = None
    
    def broadcast_message(self, msg):
        """
        Send messages to all of the players
        """
        print msg.mtype
        if (msg.mtype == Message.Type.start):
            network_msg = make_start_netmsg(msg)
        elif (msg.mtype == Message.Type.kill):
            network_msg = make_kill_netmsg(msg)
        elif (msg.mtype == Message.Type.move):
            network_msg = make_move_netmsg(msg)
        else:
            return False
        for sock in self.socks:
            sock.send(network_msg.SerializeToString())
        return True

    def get_messages(self):
        """
        Get messages from all of the players
        """
        net_msg = pb.GameMsg()
        for sock in self.socks:
            try:
                data = sock.recv(1024)
                if data:
                    net_msg.ParseFromString(data)
                    if (net_msg.mtype == pb.GameMsg.START):
                        self.message_queue.append(start_netmsg_to_msg(net_msg))
                    elif (net_msg.mtype == pb.GameMsg.KILL):
                        self.message_queue.append(kill_netmsg_to_msg(net_msg))
                    elif (net_msg.mtype == pb.GameMsg.MOVE):
                        self.message_queue.append(move_netmsg_to_msg(net_msg))
            except IOError:
                continue
        print self.message_queue
        return self.message_queue

    def start(self):
        """
        Start up the TCP connections between all of the players for messaging. This is
        handled through the network util functions. We return the player number of the
        player who we set up. 4 players must join to continue.
        """
        if (self.HOST):
            self.player, self.socks, self.addrs = establish_tcp_connections(self.HOST)
        else:
            self.player, self.socks, self.addrs = coordinate_tcp_connections()
        return self.player
