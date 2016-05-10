"""
main.py

Contains the main control flow of the game. It handles the user input
that starts the game, sets up the game window, sets up the networking
layer, and runs the main game loop.
"""

import sys, time

# Pygame is used to create the game window and render the game
import pygame

# provides the network abstraction for the game
from network_layers import NaiveNetworkLayer as network

# manages the state of the game and handles updates
from game_utils import GameState, Direction, Message, line

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
    run_time_max = 0
    run_time_min = 1
    run_time_total = 0
    frames = 0
    running = True
    send_exit = True
    while running:
        start = time.time()
        # handle network input
        for msg in network.get_messages():
            print "Got message", msg.mtype, "in ", player
            if msg.mtype == Message.Type.move:
                game.move(msg.player, msg.pos, msg.direction, start)
            elif msg.mtype == Message.Type.kill:
                game.kill(msg.player)
            elif msg.mtype == Message.Type.exit:
                running = False

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

        if game.update(player):
            game.kill(player)
            network.broadcast_message(Message.kill(player))

        # rendering
        display.fill(background_color)
        for p in game.players_left:
            for i in range(len(game.state[p])-1):
                x1, y1 = game.state[p][i]['pos']
                x2, y2 = game.state[p][i+1]['pos']
                line(display,
                     int(x1), int(y1),
                     int(x2), int(y2),
                     player_colors[p], p == player)
        pygame.display.flip()

        # exiting
        if len(game.players_left) == 0 and send_exit:
            send_exit = False
            network.broadcast_message(Message.exit(player))

        # try to maintain 60 fps
        run_time = time.time() - start
        if run_time < run_time_min:
            run_time_min = run_time
        if run_time > run_time_max:
            run_time_max = run_time
        run_time_total += run_time
        frames += 1
        sleep_time = max(1 / 60 - run_time, 0)
        time.sleep(sleep_time)

    print("GAME OVER")
    network.stop()

    print 'Effective frame rate:', frames/run_time_total
    print 'Max frame rate:', 1/run_time_min
    print 'Min frame rate:', 1/run_time_max
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
    speed = 100
    game = GameState(size,speed)
    display = pygame.display.set_mode(size)

    # ensure proper usage and parse user input
    if len(sys.argv) > 1:
        # conect to given host
        network = network(sys.argv[1])
    else:
        network = network()

    run_game(game, network, display)
