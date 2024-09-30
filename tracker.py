import socket
import sys
import random

# State variables
players = {}  # Dictionary to store registered players (name -> (IPv4, t-port, p-port, state))
games = {}  # Dictionary to store ongoing games (game_id -> (dealer, players, #holes))


# Register player
def tracker_register(player_name, player_ipv4, t_port, p_port):
    if player_name not in players:
        # Register player in tracker
        players[player_name] = (player_ipv4, t_port, p_port, "free")
        return f"SUCCESS: Player {player_name} registered."
    else:
        return f"FAILURE: Player {player_name} is already registered."


# Query all registered players
def tracker_query_players():
    if players:
        player_list = "\n".join([f"{name} -> {details[:3]}" for name, details in players.items()])
        return f"Number of registered players: {len(players)}\n{player_list}"
    else:
        return "0 players registered."


# Start game
def tracker_start_game(player_name, n, holes=9):
    print("work in progress")


# Query games(stored as a global variable so, it can be accessed)
def tracker_query_games():
    if games:
        game_list = "\n".join(
            [f"Game ID: {g_id}, Dealer: {details[0]}, Players: {details[1]}, Holes: {details[2]}" for g_id, details in
             games.items()])
        return f"Number of ongoing games: {len(games)}\n{game_list}"
    else:
        return "0 games ongoing."


# End game
def tracker_end_game(game_id, player_name):
    print("work in progress")


# De-register player command: `de-register player`
def tracker_deregister(player_name):
    if player_name in players:
        if any(player_name in game[1] or game[0] == player_name for game in games.values()):
            return "FAILURE: Player is involved in an ongoing game."
        del players[player_name]
        return f"SUCCESS: Player {player_name} de-registered."
    else:
        return "FAILURE: Player not registered."


# Process all messages sent from a player and goes to each specific command
def handle_message(message, addr):
    command = message.split()
    if command[0] == 'register':
        return tracker_register(command[1], command[2], int(command[3]), int(command[4]))
    elif command[0] == 'query' and command[1] == 'players':
        return tracker_query_players()
    elif command[0] == 'start' and command[1] == 'game':
        return tracker_start_game(command[2], int(command[3]), int(command[4]) if len(command) > 4 else 9)
    elif command[0] == 'query' and command[1] == 'games':
        return tracker_query_games()
    elif command[0] == 'end':
        return tracker_end_game(command[1], command[2])
    elif command[0] == 'de-register':
        return tracker_deregister(command[1])
    else:
        return "FAILURE: Invalid command."


# Start the tracker and listen for player commands
def start_tracker(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    print(f"Tracker running on port {port}")

    while True:
        message, addr = sock.recvfrom(1024)
        response = handle_message(message.decode(), addr)
        sock.sendto(response.encode(), addr)


# Auto runs when script is executed to start the program
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 tracker.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    start_tracker(port)
