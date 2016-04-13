import sys, random, time, copy
from enum import Enum

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
        Returns a new kill message for the the given player dies.
        """
        return Message(player, None, None, Message.Type.kill)
    
class GameState(object):
    """
    Internal representation of game state
    """
    start_pos = [(10, 10), (590, 10),
                 (590, 590), (10, 590)]
    
    start_dir = [Direction.east, Direction.south,
                 Direction.west, Direction.north]

    def __init__(self, size):
        self.players_left = [0,1,2,3]
        self.state = [[{'pos': p, 'dir': d}] for p,d in
                      zip(GameState.start_pos, GameState.start_dir)]
        self.width, self.height = size
        self.speed = 100

    def start(self):
        """
        Start the game by copying the initial position of each player into
        the last slot of their state array.
        """
        start_time = time.time()
        for p in self.players_left:
            self.state[p].append(copy.copy(self.state[p][0]))
            self.state[p][-1]['time'] = start_time

    def update(self):
        """
        Updates the game state by moving each player's position forward by
        1/60 of a second.
        Returns:
            A list of players who died in this update step.

        TODO: only check if the local player died and return a boolean.
        """
        cur_time = time.time()

        # update positions
        for p in self.players_left:
            pos = self.state[p][-1]['pos']
            d = self.state[p][-1]['dir']
            t = self.state[p][-1]['time']
            self.state[p][-1]['pos'] = d.extrapolate(pos, (cur_time - t) * self.speed)
            self.state[p][-1]['time'] = cur_time

        # check for death
        dead_players = []
        for p in self.players_left:
            curpos = self.state[p][-1]['pos']
            lastpos = self.state[p][-2]['pos']

            # check bounds
            if curpos[0] < 0 or curpos[1] < 0 or \
               curpos[0] >= self.width or curpos[1] >= self.height:
                dead_players.append(p)
                continue

            # check trail collision
            dead = False
            for p2 in self.players_left:
                r = range(len(self.state[p2])-1)
                if p == p2:
                    r = range(len(self.state[p2])-2)
                for i in r:
                    a = self.state[p2][i]['pos']
                    b = self.state[p2][i+1]['pos']
                    if self._intersect(a, b, lastpos, curpos):
                        dead = True
                        dead_players.append(p)
                        break
                if dead:
                    break
        for p in dead_players:
            self.kill(p)
        return dead_players

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
