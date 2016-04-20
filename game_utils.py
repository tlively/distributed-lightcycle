import sys, random, time, copy
from enum import Enum
import player_pb2 as pb

class Direction(Enum):
    """
    Representation of the four cardinal directions.
    """
    east = 0
    north= 1
    west = 2
    south = 3

    def extrapolate(self, loc, dist):
        """
        Returns the location `dist' units away from location `loc'.
        Args:
            loc: The (x,y) location tuple from which to extrapolate
            dist: The distance to extrapolate by
        Ret:
            The resulting (x,y) location tuple
        """
        if self == Direction.east:
            return (loc[0] + dist, loc[1])
        elif self == Direction.north:
            return (loc[0], loc[1] - dist)
        elif self == Direction.west:
            return (loc[0] - dist, loc[1])
        elif self == Direction.south:
            return (loc[0], loc[1] + dist)
        else:
            assert False
            
class Message(object):
    """
    The Message class encapsulates all of the inter-client communication
    that is exposed above the level of the Netwok Layer.
    """
    class Type(Enum):
        start = 1
        move = 2
        kill = 3

    def __init__(self, player, pos, direction, mtype):
        """
        This constructor should not be called directly. Instead, use
        Message.start, Message.move, or Message.kill.
        """
        assert direction == None or type(direction) is Direction
        self.player = player
        self.pos = pos
        self.direction = direction
        self.mtype = mtype

    @staticmethod
    def start(player):
        """
        Returns a new start message for the given player.
        """
        return Message(player, None, None, Message.Type.start)
    
    @staticmethod
    def move(player, pos, direction):
        """
        Returns a new move message for when the given player moves in the given
        direction at the given position.
        """
        return Message(player, pos, direction, Message.Type.move)

    @staticmethod
    def kill(player):
        """
        Returns a new kill message for when the given player dies.
        """
        return Message(player, None, None, Message.Type.kill)

    @staticmethod
    def deserialize(msg_str):
        """
        Create a Message from its serialized protobuf form.
        Args: msg_str - The protobuf string
        Returns: the deserialized Message
        """
        network_msg = pb.GameMsg()
        network_msg.ParseFromString(msg_str)
        player = network_msg.player_no
        pos = None
        if network_msg.HasField('pos'):
            pos = (network_msg.pos.x, network_msg.pos.y)
        direction = None
        if network_msg.HasField('dir'):
            direction = Direction(network_msg.dir)
        mtype = Message.Type(network_msg.mtype)
        return Message(player, pos, direction, mtype)

    def serialize(self):
        """
        Serializes the message as a protobuf.
        Returns: A string representing the message.
        """
        network_msg = pb.GameMsg()
        network_msg.mtype = self.mtype.value
        network_msg.player_no = self.player
        if self.pos:
            network_msg.pos.x = self.pos[0]
            network_msg.pos.y = self.pos[1]
        if self.direction:
            network_msg.dir = self.direction.value
        return network_msg.SerializeToString()
    
class GameState(object):
    """
    Internal representation of game state
    """
    def __init__(self, size=(600,600), speed=100):
        """
        Initialize GameState object.
        Args:
            size - a length,width tuple of the game board size
            speed - the speed of the players in px/sec
        """
        self.players_left = [0,1,2,3]
        
        start_pos = [(10, 10), (size[0]-10, 10),
                     (size[0]-10, size[0]-10), (10, size[0]-10)]
        
        start_dir = [Direction.east, Direction.south,
                     Direction.west, Direction.north]

        self.state = [[{'pos': p, 'dir': d}] for p,d in
                      zip(start_pos, start_dir)]
        
        self.width, self.height = size
        self.speed = speed

    def start(self):
        """
        Start the game by copying the initial position of each player into
        the last slot of their state array.
        """
        start_time = time.time()
        for p in self.players_left:
            self.state[p].append(copy.copy(self.state[p][0]))
            self.state[p][-1]['time'] = start_time

    def update(self, player):
        """
        Updates the game state by moving each player's position forward.
        Args:
            player - the local player number
        Returns:
            True if the local player should die, False otherwise
        """
        cur_time = time.time()

        last_pos = None
        if player in self.players_left:
            last_pos = self.state[player][-1]['pos']

        # update positions
        for p in self.players_left:
            pos = self.state[p][-1]['pos']
            d = self.state[p][-1]['dir']
            t = self.state[p][-1]['time']
            self.state[p][-1]['pos'] = d.extrapolate(pos, (cur_time - t) * self.speed)
            self.state[p][-1]['time'] = cur_time

        # do not do collision detection if already dead
        if player not in self.players_left:
            return False

        # check for local player death
        cur_pos = self.state[player][-1]['pos']

        # check b{ounds
        if cur_pos[0] < 0 or cur_pos[1] < 0 or \
           cur_pos[0] >= self.width or cur_pos[1] >= self.height:
            print 'bounds'
            return True

        # check trail collision
        for p2 in self.players_left:
            r = range(len(self.state[p2])-1)
            
            # modify range for colliding with self
            if player == p2:
                r = range(len(self.state[p2])-2)

            # test collision with each segment
            for i in r:
                a = self.state[p2][i]['pos']
                b = self.state[p2][i+1]['pos']
                if self._intersect(a, b, last_pos, cur_pos):
                    return True
        # don't die
        return False

    def _intersect(self, a1, a2, b1, b2):
        """
        Check for intersection between the line segment between point a1 and a2
        and the line segment between b1 and b2. The line segments must be
        either vertical or horizontal.
        Returns:
            True, if the line segments intersect,
            False, otherwise
        """
        a_vert = a1[0] == a2[0]
        b_vert = b1[0] == b2[0]

        # non-lines
        if a1 == a2 or b1 == b2:
            return False

        # both vertical, check colinearity then intersection
        if a_vert and b_vert:
            if a1[0] != b1[0]:
                return False
            return (a1[1] <= b1[1] and b1[1] <= a2[1]) or \
                (a1[1] <= b2[1] and b2[1] <= a2[1])

        # both horizontal, check colinearity then intersection
        if not a_vert and not b_vert:
            if a1[1] != b1[1]:
                return False
            return (a1[0] <= b1[0] and b1[0] <= a2[0]) or \
                (a1[0] <= b2[0] and b2[0] <= a2[0])

        # special case for continuation
        if a2 == b1:
            return False

        # a vertical, b horizontal
        if a_vert:
            return min(a1[1],a2[1]) <= b1[1] and b1[1] <= max(a1[1],a2[1]) and \
                min(b1[0],b2[0]) <= a1[0] and a1[0] <= max(b1[0],b2[0])

        # b vertical, a horizontal
        return min(b1[1],b2[1]) <= a1[1] and a1[1] <= max(b1[1],b2[1]) and \
            min(a1[0],a2[0]) <= b1[0] and b1[0] <= max(a1[0],a2[0])

    def move(self, player, pos, direction, time):
        """
        Update the last point in the player's history and then create a
        new last point.
        """
        if self.state[player]:
            self.state[player][-1]['pos'] = pos
            self.state[player][-1]['dir'] = direction
            self.state[player][-1]['time'] = time
            self.state[player].append(copy.copy(self.state[player][-1]))

    def kill(self, player):
        """
        Remove the given player from the game.
        """
        if player in self.players_left:
            self.players_left.remove(player)
            self.state[player] = []
