import time, random
import socket as sock
import player_pb2 as pb
import paxosmsg_pb2 as pxb
from select import select
import cPickle

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

    def start(self):
        """
        Perform setup and block until the game is supposed to begin.
        """
        while True:
            pass

    def stop(self):
        """
        Perform teardown
        """
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
    no agreement algorithm for game state. Should show liveness but might
    show inconsistencies.
    """

    def __init__(self, HOST=None):
        self.HOST = HOST
        # These get initialized in start
        self.player = None
        self.socks = None
        self.addrs = None

    def broadcast_message(self, msg):
        """
        Send messages to all of the players
        """
        network_msg = msg.serialize()
        for i, s in enumerate(self.socks):
            if s:
                try:
                    s.send(network_msg)
                except sock.error:
                    print 'lost connection to', i
                    self.socks[i] = None
        return True

    def get_messages(self):
        """
        Get messages from all of the players
        """
        msgs = []
        net_msg = pb.GameMsg()
        for s in self.socks:
            if s:
                try:
                    data = s.recv(1024)
                    if data:
                        msgs.append(Message.deserialize(data))
                except IOError:
                    continue
        return msgs

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

class PartTimeNetworkLayer(NetworkLayer):
    """
    A NetworkLayer implementation that uses Paxos }:-) for consistency with stable leaders and heartbeats.
    """
    def __init__(self, HOST=None):
        self.HOST = HOST
        # These get initialized in start
        self.player = None
        self.socks = None
        self.addrs = None

    def broadcast_message(self, msg):
        """
        Send messages to all of the players
        """
        with self.lock:
            self.outbox.append(msg.serialize())

    def _broadcast_message(self, msg):
        """
        Put msg over all of the sockets
        """
        for i, s in enumerate(self.socks):
            if s:
                try:
                    msg.from_uid = self.node.node_uid
                    msg.instance = self.instance
                    s.send(msg.SerializeToString())
                except sock.error:
                    print 'lost connection to', i
                    self.socks[i] = None
        return True

    def _send_message(self, to, msg):
        """
        Put msg to socket belonging to UID to
        """
        try:
            msg.from_uid = self.node.node_uid
            msg.instance = self.instance
            self.socks[to].send(msg.SerializeToString())
        except sock.error:
            print 'lost connection'


    def get_messages(self):
        """
        Get accepted messages from all of the players
        """
        with self.lock:
            inbox = self.inbox
            self.inbox = []
        if inbox: print inbox, map(Message.deserialize, inbox)
        return map(Message.deserialize, inbox)

    def _get_messages(self):
        """
        Read from all of the sockets
        """
        msgs = []
        for s in self.socks:
            if s:
                try:
                    data = s.recv(1024)
                    if data:
                        msg = pxb.msg()
                        msg.ParseFromString(data)
                        if msg.instance > self.instance:
                            print "OLD"
                        msgs.append((s,msg))
                except IOError:
                    continue
        return msgs

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
        self.call_part_time_parliament_to_order()
        return self.player

    def stop(self):
        self.running = False

    def call_part_time_parliament_to_order(self):
        """
        Initialize Paxos algorithm, with self as Node # uid, and spawn its thread
        """
        import paxos.functional
        def status(*args):
            print self.node.node_uid, args
        class MyMessenger(paxos.functional.HeartbeatMessenger):
            def __init__(_self): return super(MyMessenger,_self).__init__()
            def send_prepare(_self, proposal_id):
                '''
                Broadcasts a Prepare message to all Acceptors
                '''
                status("Preparing", proposal_id)
                msg = pxb.msg()
                msg.type = pxb.PREPARE
                msg.proposal_id = cPickle.dumps(proposal_id)
                self._broadcast_message(msg)

            def send_promise(_self, proposer_uid, proposal_id, previous_id, accepted_value):
                '''
                Sends a Promise message to the specified Proposer
                '''
                status("Promising", proposal_id, accepted_value)
                msg = pxb.msg()
                msg.type = pxb.PROMISE
                msg.proposal_id = cPickle.dumps(proposal_id)
                if previous_id:
                    msg.previous_id = cPickle.dumps(previous_id)
                msg.value = cPickle.dumps(accepted_value)
                self._send_message(proposer_uid, msg)

            def send_accept(_self, proposal_id, proposal_value):
                '''
                Broadcasts an Accept! message to all Acceptors
                '''
                status("Accept!ing", proposal_id, proposal_value)
                msg = pxb.msg()
                msg.type = pxb.ACCEPT
                msg.proposal_id = cPickle.dumps(proposal_id)
                msg.value = cPickle.dumps(proposal_value)
                self._broadcast_message(msg)

            def send_accepted(_self, proposal_id, accepted_value):
                '''
                Broadcasts an Accepted message to all Learners
                '''
                status("Accepting", proposal_id, accepted_value)
                msg = pxb.msg()
                msg.type = pxb.ACCEPTED
                msg.proposal_id = cPickle.dumps(proposal_id)
                msg.value = cPickle.dumps(accepted_value)
                self._broadcast_message(msg)

            def on_resolution(_self, proposal_id, value):
                '''
                Called when a resolution is reached
                '''
                status("Accepted", proposal_id, value)
                if proposal_id.uid == self.node.node_uid:
                    with self.lock:
                        self.outbox = self.outbox[len(value):]
                with self.lock:
                    self.inbox.extend(value)
                self.incr_instance = True

            def send_prepare_nack(_self, to_uid, proposal_id, promised_id):
                '''
                Sends a Prepare Nack message for the proposal to the specified node
                '''
                status("Prepare Nack", proposal_id, promised_id)
                msg = pxb.msg()
                msg.type = pxb.NACK_PREPARE
                msg.proposal_id = cPickle.dumps(proposal_id)
                msg.previous_id = cPickle.dumps(promised_id)
                self._send_message(to_uid, msg)

            def send_accept_nack(_self, to_uid, proposal_id, promised_id):
                '''
                Sends a Accept! Nack message for the proposal to the specified node
                '''
                status("Accept Nack", proposal_id, promised_id)
                msg = pxb.msg()
                msg.type = pxb.NACK_ACCEPT
                msg.proposal_id = cPickle.dumps(proposal_id)
                msg.previous_id = cPickle.dumps(promised_id)
                self._send_message(to_uid, msg)

            def on_leadership_acquired(_self):
                '''
                Called when leadership has been aquired. This is not a guaranteed
                position. Another node may assume leadership at any time and it's
                even possible that another may have successfully done so before this
                callback is exectued. Use this method with care.

                The safe way to guarantee leadership is to use a full Paxos instance
                whith the resolution value being the UID of the leader node. To avoid
                potential issues arising from timing and/or failure, the election
                result may be restricted to a certain time window. Prior to the end of
                the window the leader may attempt to re-elect itself to extend it's
                term in office.
                '''
                status("I'm the leader!")

            def send_heartbeat(_self, leader_proposal_id):
                '''
                Sends a heartbeat message to all nodes
                '''
                status("My heart still beats", leader_proposal_id)
                msg = pxb.msg()
                msg.type = pxb.HEARTBEAT
                msg.proposal_id = cPickle.dumps(leader_proposal_id)
                self._broadcast_message(msg)

            def schedule(_self, msec_delay, func_obj):
                '''
                While leadership is held, this method is called by pulse() to schedule
                the next call to pulse(). If this method is not overridden appropriately,
                subclasses must use the on_leadership_acquired()/on_leadership_lost() callbacks
                to ensure that pulse() is called every hb_period while leadership is held.
                '''
                self.node.next_hb = time.time() + msec_delay

            def on_leadership_lost(_self):
                '''
                Called when loss of leadership is detected
                '''
                status("I'm not the leader :(")

            def on_leadership_change(_self, prev_leader_uid, new_leader_uid):
                '''
                Called when a change in leadership is detected. Either UID may
                be None.
                '''
                status("Leader change", prev_leader_uid, new_leader_uid)

        self.messenger = MyMessenger()
        self.node = paxos.functional.HeartbeatNode(self.messenger, self.player, len(self.socks)/2 + 1)
        self.inbox = []
        self.outbox = []
        self.running = True
        self.instance = 1
        self.incr_instance = False

        def do_paxos(self):
            """
            Main Paxos loop, runs in own thread
            """
            while self.running:
                for s,msg in self._get_messages():
                    proposal_id = paxos.functional.ProposalID._make(cPickle.loads(str(msg.proposal_id)))
                    if msg.previous_id:
                            previous_id = paxos.functional.ProposalID._make(cPickle.loads(str(msg.previous_id)))
                    self.node.next_proposal_number = max(self.node.next_proposal_number, proposal_id.number + 1)
                    if msg.type == pxb.PREPARE:
                        self.node.recv_prepare(msg.from_uid, proposal_id)
                    elif msg.type == pxb.PROMISE:
                        previous_id = None
                        accepted_value = cPickle.loads(str(msg.value))
                        self.node.recv_promise(msg.from_uid, proposal_id, previous_id, accepted_value)
                    elif msg.type == pxb.ACCEPT:
                        self.node.recv_accept_request(msg.from_uid, proposal_id, cPickle.loads(str(msg.value)))
                    elif msg.type == pxb.ACCEPTED:
                        self.node.recv_accepted(msg.from_uid, proposal_id, cPickle.loads(str(msg.value)))
                    elif msg.type == pxb.NACK_PREPARE:
                        self.node.recv_prepare_nack(msg.from_uid, proposal_id, previous_id)
                    elif msg.type == pxb.NACK_ACCEPT:
                        self.node.recv_accept_nack(msg.from_uid, proposal_id, previous_id)
                    elif msg.type == pxb.HEARTBEAT:
                        self.node.recv_heartbeat(msg.from_uid, proposal_id)
                    else:
                        raise NotImplementedError
                if not self.incr_instance:
                    with self.lock:
                        outbox = self.outbox
                    if outbox and not self.node.proposed_value:
                        self.node.proposed_value = outbox
                        self.node.prepare()
                    self.node.persisted()
                    if self.node.leader and self.node.next_hb <= time.time():
                        self.node.pulse()
                else:
                    self.node = paxos.functional.HeartbeatNode(self.messenger, self.player, len(self.socks)/2 + 1)
                    self.instance += 1
                    self.incr_instance = False

        import thread
        self.lock = thread.allocate_lock()
        self.paxos = thread.start_new_thread(do_paxos, tuple([self]))
