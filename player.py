import socket
import sys

player_name = None 


tracker_ip = ""
tracker_port = ""
p_port = ""



def make_socket_non_blocking(sock):
    fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
    return sock

def listen_for_broadcast(p_port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', p_port))  # Listen on the player's p-port
    sock = make_socket_non_blocking(sock)

    while True:
        try:
            message, _ = sock.recvfrom(1024)
            return message.decode()
        except BlockingIOError:
            continue


def send_command(tracker_ip, tracker_port, command):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(command.encode(), (tracker_ip, tracker_port))
    response, _ = sock.recvfrom(1024)
    print(f"Tracker Response: {response.decode()}")


def forward_game_table(game_table):
    """
    Forward the game table from the dealer to all players.
    """
    global player_table
    player_table = eval(game_table.split('|')[1])  # Extract and store the player table
    print(f"Received game table: {player_table}")

    for player in player_table:
        if player[0] != player_name:  # Don't forward to self
            player_ip, player_p_port = player[1], player[2]
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(f"GAME_TABLE|{player_table}".encode(), (player_ip, player_p_port))
            print(f"Forwarded game table to {player[0]} at {player_ip}:{player_p_port}")

def auto_join_game(p_port):
    """Automatically joins the game when a broadcast message is received."""
    while True:
        message = listen_for_broadcast(p_port)
        if "GAME_STARTED" in message:
            print(f"Received broadcast message: {message}")
            forward_game_table(message)  # If dealer, forward table to other players
            print("You are now entering the game.")
            in_game_loop(tracker_ip, tracker_port)
        elif "GAME_TABLE" in message:
            print(f"Received game table: {message}")
            player_table = eval(message.split('|')[1])  # Extract the player table
            print(f"Joined the game with players: {player_table}")
            in_game_loop(tracker_ip, tracker_port)


def take_turn(tracker_ip, tracker_port):
    """
    Handle the player's turn.
    1. Draw a card (either from stock or discard pile).
    2. Swap or discard the drawn card.
    """
    global player_name
    try:
        # Draw a card from stock or discard
        draw_choice = input("Draw from stock or discard pile? (stock/discard): ").strip().lower()
        if draw_choice not in ["stock", "discard"]:
            print("Invalid choice. Please choose 'stock' or 'discard'.")
            return

        # Send the draw command to the tracker
        response = send_command(tracker_ip, tracker_port, f"draw {player_name} {draw_choice}")
        print(f"Tracker Response: {response}")

        # Ensure the response contains both drawn card and player's hand
        if '|' not in response:
            print(f"Error: Invalid response format from tracker: {response}")
            return

        # Tracker should return the drawn card and current hand
        parts = response.split('|')
        if len(parts) < 2:
            print(f"Error: Incomplete response from tracker. Got: {response}")
            return

        drawn_card = parts[0]  # The drawn card
        player_hand = eval(parts[1])  # The current player's hand (list of dicts)

        # Display the current hand
        print("Your current hand:")
        for card in player_hand:
            if card["face_up"]:
                print(f"{card['rank']}{card['suit']}", end=" ")
            else:
                print("***", end=" ")
        print()

        # Decide to swap or discard
        action = input(f"You drew {drawn_card}. Do you want to swap or discard? (swap/discard): ").strip().lower()
        if action == "swap":
            # Player chooses which face-down card to swap
            face_down_indices = [i for i, card in enumerate(player_hand) if not card["face_up"]]
            if face_down_indices:
                swap_choice = int(input(f"Choose a face-down card to swap (positions: {face_down_indices}): "))
                if swap_choice in face_down_indices:
                    response = send_command(tracker_ip, tracker_port, f"swap {player_name} {drawn_card} {swap_choice}")
                    print(f"Tracker Response: {response}")
                else:
                    print("Invalid choice. No swap performed.")
            else:
                print("No face-down cards to swap.")
        elif action == "discard":
            # Send discard command to the tracker
            response = send_command(tracker_ip, tracker_port, f"discard {player_name} {drawn_card}")
            print(f"Tracker Response: {response}")
        else:
            print("Invalid action. No discard or swap performed.")
    except Exception as e:
        print(f"An error occurred during your turn: {e}")

def in_game_loop(tracker_ip, tracker_port):
    """
    The in-game loop for players. Only accessible when the player is "in-play".
    """
    global player_name
    while True:
        print("\nIn-game Commands: [take turn, end game, exit]")
        user_input = input("Enter a command: ")

        if user_input == "exit":
            break

        if user_input == "take turn":
            take_turn(tracker_ip, tracker_port)

        elif user_input.startswith("end game"):
            parts = user_input.split()
            if len(parts) == 3:
                response = send_command(tracker_ip, tracker_port, f'end {parts[1]} {parts[2]}')
                print(f"Tracker Response: {response}")
                if "SUCCESS" in response:
                    return  # Exit in-game loop and go back to pre-game loop
            else:
                print("Invalid format.")
        else:
            print("Unknown command.")

def pre_game_loop(tracker_ip, tracker_port, p_port):
    """
    The pre-game loop for players. Accessible when the player is "free".
    """
    global player_name
    listener_thread = threading.Thread(target=auto_join_game, args=(p_port,), daemon=True)
    listener_thread.start()  # Start listening for broadcast messages

    while True:
        print("\nPre-game Commands: [register, query players, start game, query games, de-register, exit]")
        user_input = input("Enter a command: ")

        if user_input == "exit":
            break

        # Pre-game commands
        if user_input.startswith("register"):
            parts = user_input.split()
            if len(parts) == 5:
                player_name = parts[1]  # Store the player name when registering
                command = f"register {parts[1]} {parts[2]} {parts[3]} {parts[4]}"
                print(f"Tracker Response: {send_command(tracker_ip, tracker_port, command)}")
            else:
                print("Invalid format. [player_name, player_ipv4, t_port, p_port]")
        elif user_input == "query players":
            print(f"Tracker Response: {send_command(tracker_ip, tracker_port, 'query players')}")

        elif user_input.startswith("start game"):

            if player_name is None:
                print("You must register before starting a game.")
            else:
                parts = user_input.split()
                if len(parts) == 4:
                    response = send_command(tracker_ip, tracker_port, f'start game {player_name} {parts[2]} {parts[3]}')
                    print(f"Tracker Response: {response}")
                    if "SUCCESS" in response:
                        in_game_loop(tracker_ip, tracker_port)  # Enter the in-game loop
                else:
                    print("Invalid format. Use: start game <Dealer> <#players(excluding dealer)> <#holes>")

        elif user_input == "query games":
            print(f"Tracker Response: {send_command(tracker_ip, tracker_port, 'query games')}")

        elif user_input.startswith("de-register"):
            if player_name is None:
                print("You must register before de-registering.")
                continue
            print(f"Tracker Response: {send_command(tracker_ip, tracker_port, f'de-register {player_name}')}")

        else:
            print("Unknown command.")


def auto_join_game(p_port):
    """Automatically joins the game when a broadcast message is received."""
    while True:
        message = listen_for_broadcast(p_port)
        if "Game" in message and "started" in message:
            print(f"Received broadcast message: {message}")
            # Automatically enter the game loop
            print("You are now entering the game.")
            in_game_loop(tracker_ip, tracker_port)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 player.py <tracker_ip> <tracker_port> <p-port>")
        sys.exit(1)

    tracker_ip = sys.argv[1]
    tracker_port = int(sys.argv[2])
    p_port = int(sys.argv[3])

    # Start the pre-game loop
    pre_game_loop(tracker_ip, tracker_port, p_port)
