import socket
import threading
import pickle

# Server-Socket erstellen
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 5555))
server.listen(4)  # Maximale Anzahl an Spielern (4)

players = []
player_sockets = []  # Store the socket references separately
players_lock = threading.Lock()

# Funktion, die mit jedem Client kommuniziert
def handle_client(client, player):
    global players, player_sockets
    print(f"Player {player} connected")
    
    try:
        while True:
            try:
                data = client.recv(2048)
                if not data:
                    break  # If no data is received, the client has disconnected
                players_data = pickle.loads(data)

                # Lock the players list while updating it
                with players_lock:
                    players[player] = players_data

                # Send updated players' data to all clients
                with players_lock:
                    for p_client in player_sockets:
                        p_client.send(pickle.dumps(players))

            except ConnectionResetError:
                print(f"Connection reset by player {player}")
                break  # This handles the WinError 10054 case (client disconnected unexpectedly)

    except Exception as e:
        print(f"Error with player {player}: {e}")
    finally:
        # Notify other players about the disconnection
        with players_lock:
            # Ensure the player is still in the list before attempting to remove them
            if player < len(players):
                disconnected_player_data = players.pop(player)
                player_sockets.pop(player)  # Remove the player's socket
                print(f"Player {player} disconnected")
            
            # Send disconnection notification to other clients
            for p_client in player_sockets:
                p_client.send(pickle.dumps({"disconnected": player}))

        client.close()

# Verbindungsaufbau und -verwaltung
def start():
    print("Server is running...")
    
    while True:
        client, address = server.accept()
        print(f"Connection from {address} has been established.")
        
        # Füge den neuen Spieler zur Liste hinzu
        player = len(players)
        players.append({"x": 400, "y": 400, "rot_angle": 0, "image": "Player.png"})  # Startposition und Bild des Spielers
        player_sockets.append(client)  # Store the player's socket
        
        thread = threading.Thread(target=handle_client, args=(client, player))
        thread.start()

start()
