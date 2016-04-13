import time, random

from game_utils import GameState, Direction, Message

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
