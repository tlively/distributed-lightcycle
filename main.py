import sys, time

# Pygame is used to create the game window and render the game
import pygame
from pygame import gfxdraw

# provides the network abstraction for the game
from network_layers import NaiveNetworkLayer as network

# manages the state of the game and handles updates
from game_utils import GameState, Direction, Message

# Map keyboard input to directions
keyboard_directions = {pygame.K_w: Direction.north,
                       pygame.K_UP: Direction.north,
                       pygame.K_a: Direction.west,
                       pygame.K_LEFT: Direction.west,
                       pygame.K_s: Direction.south,
                       pygame.K_DOWN: Direction.south,
                       pygame.K_d: Direction.east,
                       pygame.K_RIGHT: Direction.east}

# The colors used to draw each player
player_colors = [pygame.Color('red'),
                 pygame.Color('blue'),
                 pygame.Color('green'),
                 pygame.Color('yellow')]

# The background color of the field
background_color = pygame.Color('black')

def run_game(game, network, display):
    """
    The main game loop. Waits for the network layer to signal the start of
    the game then runs an iteration of the game loop 60 times per second.
    The game loop polls for local input, which it submits to the network for
    verification, then it polls for input from the network layer and updates
    the game state accordingly. Finally it renders the frame. The game loop
    exits when there are no players left in the game.
    """
    
    # wait for the game to start
    player = network.start()
    game.start()

    # main game loop
    while len(game.players_left) > 0:
        start = time.time()
        # handle network input
        for msg in network.get_messages():
            if msg.mtype == Message.Type.move:
                game.move(msg.player, msg.pos, msg.direction, start)
            elif msg.mtype == Message.Type.kill:
                # TODO: change GameState::update to only check local
                # player's death so that these messages are important
                game.kill(msg.player)

        # handle local events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                network.broadcast_message(Message.kill(player))
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and player in game.players_left:
                key = event.key
                d = keyboard_directions.get(key)
                if d == None or d == game.state[player][-1]['dir']:
                    continue
                pos = game.state[player][-1]['pos']
                msg = Message.move(player, pos, Direction(d))
                network.broadcast_message(msg)

        if player in game.update():
            network.broadcast_message(Message.kill(player))

        # rendering
        display.fill(background_color)
        for p in game.players_left:
            for i in range(len(game.state[p])-1):
                x1, y1 = game.state[p][i]['pos']
                x2, y2 = game.state[p][i+1]['pos']
                gfxdraw.line(display,
                             int(x1), int(y1),
                             int(x2), int(y2),
                             player_colors[p])
        pygame.display.flip()

        # try to maintain 60 fps
        sleep_time = max(1 / 60 - (time.time() - start), 0)
        time.sleep(sleep_time) 

    print("GAME OVER")
    sys.exit()

if __name__ == '__main__':
    """
    Initialize the components of the game and start the game loop.
    First check that the user is beginning the game properly.

    Currently, the first player to start the game has to input 1
    as the player number and the IP and PORT to set up the game
    on. All other players connect with that same IP and PORT, and
    use player numbers 2-3. No more than 4 players in a game.

    Usage: python main.py [IP]

    (If IP not given, it is assumed you are setting up the connections)
    """
    # set up game display
    pygame.init()
    size = (600,600)
    game = GameState(size)
    display = pygame.display.set_mode(size)

    # ensure proper usage and parse user input
    if len(sys.argv) > 1:
        # conect to given host
        network = network(sys.argv[1])
    else:
        network = network()
 
    run_game(game, network, display)
