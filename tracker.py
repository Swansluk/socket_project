import socket
import sys
import random

# State variables
players = {}  # Dictionary to store registered players (name -> (IPv4, t-port, p-port, state))
games = {}  # Dictionary to store ongoing games (game_id -> (dealer, players, #holes))

def make_socket_non_blocking(sock):
    fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
    return sock

# Broadcast message to all players in the game
def broadcast_to_players(game_id, message):
    game = games[game_id]
    for player in game['players']:
        player_ip, player_p_port = players[player][0], int(players[player][2])  # Get player's IPv4 and p-port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), (player_ip, player_p_port))
        sock.close()
def check_game_status(player_name):
    """
    Check if the player is involved in an active game.
    """
    for game_id, game_info in games.items():
        if player_name in game_info['players']:
            return "SUCCESS: Game is active."
    return "FAILURE: No game started for this player."

def check_player_state(player_name):
    if player_name in players:
        return players[player_name][3]  # This returns either 'free' or 'in-play'
    return "FAILURE: Player not registered."

def create_deck():
    suits = ['C', 'D', 'H', 'S']  # Clubs, Diamonds, Hearts, Spades
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    deck = [{"rank": rank, "suit": suit, "face_up": False} for suit in suits for rank in ranks]
    return deck

# Deal cards to players
def deal_cards(players):
    deck = create_deck()
    random.shuffle(deck)
    hands = {}

    for player in players:
        # Give 6 cards to each player
        player_hand = [deck.pop(0) for _ in range(6)]
        # Set 2 cards face-up randomly
        face_up_indices = random.sample(range(6), 2)
        for index in face_up_indices:
            player_hand[index]["face_up"] = True
        hands[player] = player_hand

    discard_pile = [deck.pop(0)]  # First card goes to the discard pile
    stock_pile = deck  # Remaining cards become the stock pile

    return hands, discard_pile, stock_pile

def end_game(game_id):
    game = games[game_id]
    scores = {player: calculate_score(game["player_hands"][player]) for player in game["players"]}
    winner = min(scores, key=scores.get)  # Player with the lowest score wins
    print(f"Game over! The winner is {winner} with {scores[winner]} points.")

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
        if player_name not in players or players[player_name][3] != "free":
        return f"FAILURE: Player {player_name} is not available to start a game."

    free_players = [p for p, d in players.items() if d[3] == "free" and p != player_name]
    if len(free_players) < n:
        return f"FAILURE: Not enough free players to start the game. Need {n}, but only {len(free_players)} available."


    selected_players = random.sample(free_players, n)
    selected_players.insert(0, player_name)  # Include the dealer in the list of players


    for player in selected_players:
        players[player] = (*players[player][:3], "in-play")


    game_id = f"game_{len(games) + 1}"
    games[game_id] = (player_name, selected_players, holes)

    game_id = f"Game_{len(games) + 1}"
    hands, discard_pile, stock_pile = deal_cards(selected_players)
    games[game_id] = {
        "dealer": player_name,
        "players": selected_players,
        "player_hands": hands,
        "discard_pile": discard_pile,
        "stock_pile": stock_pile,
        "holes": holes
    }
    broadcast_to_players(game_id, f"Game {game_id} has started")

    return f"SUCCESS: Game {game_id} started with players {selected_players} for {holes} holes."




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
       if game_id in games and games[game_id][0] == player_name:
        # Mark all players in this game as "free"
        for player in games[game_id][1]:
            players[player] = (*players[player][:3], "free")

        del games[game_id]  # Remove the game
        return f"SUCCESS: Game {game_id} ended."
    else:
        return f"FAILURE: Game {game_id} not found or {player_name} is not the dealer."


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
