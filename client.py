
import pygame
import socket
import pickle

# Pygame initialisieren
pygame.init()

# Fenstergröße und Anzeige
WIN_WIDTH, WIN_HEIGHT = 1000, 1000
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Online Game")

# Spieler-Steuerung
VEL = 3
ROT_MAX = 15  
ROT_SPEED = 3

# Netzwerkverbindung
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 5555))

# Spielerklasse
class Player:
    def __init__(self, x_pos, y_pos,  rot_angle, image_path="Player.png"):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x = 0
        self.y = 0
        self.rot_angle = rot_angle
        self.image_path = image_path
        try:
            self.image = pygame.image.load(self.image_path)
            self.image = pygame.transform.scale(self.image, (250, 250))
        except pygame.error:
            print("Player.png konnte nicht geladen werden.")
            self.image = pygame.Surface((150, 150))
            self.image.fill((0, 255, 0))

    def draw(self, win):
        rotated_image = pygame.transform.rotate(self.image, -self.rot_angle)
        new_rect = rotated_image.get_rect(center=(self.x_pos, self.y_pos))
        win.blit(rotated_image, new_rect.topleft)

    def move(self, keys):
        if keys[pygame.K_w]:
            self.y -= VEL
        if keys[pygame.K_s]:
            self.y += VEL
        if keys[pygame.K_a]:
            self.x -= VEL
            self.rot_angle = max(-ROT_MAX, self.rot_angle - ROT_SPEED)
        elif keys[pygame.K_d]:
            self.x += VEL
            self.rot_angle = min(ROT_MAX, self.rot_angle + ROT_SPEED)
        else:
            # Rotation zur Mitte
            if self.rot_angle > 0:
                self.rot_angle = max(0, self.rot_angle - ROT_SPEED)
            elif self.rot_angle < 0:
                self.rot_angle = min(0, self.rot_angle + ROT_SPEED)

        self.x_pos += self.x
        self.y_pos += self.y

        # Dämpfung der Bewegung
        self.x *= 0.86
        self.y *= 0.86

        # Begrenzung des Spielfelds
        self.x_pos = max(0, min(WIN_WIDTH, self.x_pos))
        self.y_pos = max(0, min(WIN_HEIGHT, self.y_pos))

def display_text(text, position, font_size=30, color=(255, 0, 0)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.bottomright = position  # Position in the bottom right corner
    screen.blit(text_surface, text_rect)
    
def show_disconnected_message(player_id):
    message = f"Player {player_id} has disconnected."
    display_text(message, (WIN_WIDTH - 10, WIN_HEIGHT - 10))

# Netzwerkkommunikation
def send_position(player_data):
    data = pickle.dumps(player_data)
    client.send(data)   
    

def receive_positions():
    try:
        data = client.recv(2048)
        if not data:
            print("Server disconnected.")
            return []
        players = pickle.loads(data)
        return players
    except (ConnectionResetError, ConnectionAbortedError) as e:
        print(f"Error receiving data: {e}")
        return []

def main():
    player = Player(400, 400, 0)  # Startposition des Spielers
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  # Stop the game loop if the window is closed

        if not running:
            break  # Exit if the window is closed

        screen.fill((149, 224, 237))  # Hintergrundfarbe

        keys = pygame.key.get_pressed()

        # Bewegung des Spielers
        player.move(keys)

        # Sende die Position an den Server
        send_position({"x": player.x_pos, "y": player.y_pos, "rot_angle": player.rot_angle, "image": "Player.png"})

        # Empfange die Positionen der anderen Spieler
        players = receive_positions()
        if not players:
            break  # Exit the loop if no players are returned (connection lost)

        # Zeichne die anderen Spieler mit ihren eigenen Bildern
        for p in players:
            other_player = Player(p["x"], p["y"], p["rot_angle"], p["image"])
            other_player.draw(screen)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()  # Properly quit Pygame after the game loop is done

# Spiel starten
if __name__ == "__main__":
    main()