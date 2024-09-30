import socket
import sys


def send_command(tracker_ip, tracker_port, command):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(command.encode(), (tracker_ip, tracker_port))
    response, _ = sock.recvfrom(1024)
    print(f"Tracker Response: {response.decode()}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 player.py <tracker_ip> <tracker_port>")
        sys.exit(1)

    tracker_ip = sys.argv[1]
    tracker_port = int(sys.argv[2])

    # Start the command loop
    while True:
        print("\nCommands: [register, query players, start game, query games, end, de-register, exit]")
        user_input = input("Enter a command: ")

        # Exit the loop if the user types "exit"
        if user_input == "exit":
            break

        # Check if the user wants to register
        elif user_input.startswith("register"):
            parts = user_input.split()
            if len(parts) == 5:
                # Registration command: register <player> <IPv4> <t-port> <p-port>
                player_name = parts[1]
                ipv4 = parts[2]
                t_port = parts[3]
                p_port = parts[4]
                command = f"register {player_name} {ipv4} {t_port} {p_port}"
                send_command(tracker_ip, tracker_port, command)
            else:
                print("Invalid format. Use: register <player> <IPv4> <t-port> <p-port>")

        # Other commands
        elif user_input == "query players":
            send_command(tracker_ip, tracker_port, 'query players')

        elif user_input.startswith("start game"):
            parts = user_input.split()
            if len(parts) == 4:
                send_command(tracker_ip, tracker_port, f'start game {parts[1]} {parts[2]} {parts[3]}')
            else:
                print("Invalid command format. Use: start game <n> <#holes>")

        elif user_input == "query games":
            send_command(tracker_ip, tracker_port, 'query games')

        elif user_input.startswith("end"):
            parts = user_input.split()
            if len(parts) == 3:
                send_command(tracker_ip, tracker_port, f'end {parts[1]} {parts[2]}')
            else:
                print("Invalid command format. Use: end <game-identifier>")

        elif user_input == "de-register":
            parts = user_input.split()
            if len(parts) == 2:
                send_command(tracker_ip, tracker_port, f'de-register {parts[1]}')
            else:
                print("Invalid command format. Use: de-register <player>")

        else:
            print("Unknown command.")