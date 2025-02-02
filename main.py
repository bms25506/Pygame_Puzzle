import pygame
import sys
import random
import os
import tkinter as tk
from tkinter import filedialog

# ----------------------------
# Configuration
# ----------------------------
# Grid size (number of rows and columns)
GRID_ROWS = 3
GRID_COLS = 3

# How close (in pixels) a piece must be to its target position to snap into place.
SNAP_DISTANCE = 20

# Screen dimensions (you can adjust as needed)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# ----------------------------
# PuzzlePiece Class
# ----------------------------
class PuzzlePiece:
    def __init__(self, image, correct_pos):
        """
        image: A pygame.Surface representing the piece image.
        correct_pos: The (x, y) tuple for the piece's correct top-left position.
        """
        self.image = image
        self.correct_pos = correct_pos  # The target location
        self.rect = self.image.get_rect(topleft=correct_pos)  # Current position (will be randomized later)
        self.moving = False  # Is the piece currently being dragged?
    
    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
    
    def update_position(self, pos):
        # Update the top-left corner based on the mouse position (adjust so the piece centers under the mouse)
        self.rect.center = pos

    def snap_to_place(self):
        # If the piece is close enough to its target, snap it exactly into place.
        correct_x, correct_y = self.correct_pos
        current_x, current_y = self.rect.topleft
        if abs(current_x - correct_x) < SNAP_DISTANCE and abs(current_y - correct_y) < SNAP_DISTANCE:
            self.rect.topleft = self.correct_pos
            return True
        return False

# ----------------------------
# Utility Functions
# ----------------------------
def load_image(path):
    """Load an image from the given path and convert it for Pygame."""
    if not os.path.exists(path):
        print(f"Image file not found: {path}")
        sys.exit()
    image = pygame.image.load(path)
    return image.convert_alpha()

def ask_user_for_image():
    """Use Tkinter’s file dialog to let the user choose an image."""
    root = tk.Tk()
    root.withdraw()  # Hide the main Tk window.
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files", "*.*")]
    )
    return file_path

def create_puzzle_pieces(image, grid_rows, grid_cols, start_pos=(50, 50)):
    """
    Cuts the image into grid_rows x grid_cols pieces.
    start_pos: The top-left position on the screen where the complete puzzle would be placed.
    Returns a list of PuzzlePiece objects.
    """
    pieces = []
    image_width, image_height = image.get_size()
    piece_width = image_width // grid_cols
    piece_height = image_height // grid_rows

    # Create pieces by slicing the image.
    for row in range(grid_rows):
        for col in range(grid_cols):
            # Define the area of the piece on the original image.
            rect = pygame.Rect(col * piece_width, row * piece_height, piece_width, piece_height)
            # Extract the piece image.
            piece_image = image.subsurface(rect).copy()
            # Determine the correct on-screen position
            correct_x = start_pos[0] + col * piece_width
            correct_y = start_pos[1] + row * piece_height
            piece = PuzzlePiece(piece_image, (correct_x, correct_y))
            pieces.append(piece)
    return pieces

def shuffle_pieces(pieces, screen_rect):
    """
    Randomly repositions the pieces somewhere on the screen (outside of the puzzle area, if desired).
    For simplicity, we randomly place them in the available screen area.
    """
    for piece in pieces:
        # Random top-left position (ensure the whole piece is within the screen boundaries)
        piece.rect.x = random.randint(0, screen_rect.width - piece.rect.width)
        piece.rect.y = random.randint(0, screen_rect.height - piece.rect.height)

# ----------------------------
# Main Function
# ----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Jigsaw Puzzle")
    clock = pygame.time.Clock()

    # ----------------------------
    # Image Selection
    # ----------------------------
    # For pre-programmed images, you might have a folder (e.g., "images/")
    # For now, let’s ask the user if they want to load their own image.
    use_custom_image = input("Do you want to load your own image? (y/n): ").strip().lower() == 'y'
    if use_custom_image:
        image_path = ask_user_for_image()
        if not image_path:
            print("No image selected. Exiting.")
            sys.exit()
    else:
        # Use a pre-programmed image in the project folder.
        image_path = os.path.join("images", "default.jpg")  # Make sure you have an images/default.jpg file.
    
    original_image = load_image(image_path)

    # Optionally, scale the image if it’s too large.
    # For this example, we scale it to a maximum width/height of 400 pixels.
    max_dimension = 400
    iw, ih = original_image.get_size()
    scale = min(max_dimension/iw, max_dimension/ih, 1)  # Do not upscale if image is smaller.
    if scale < 1:
        new_size = (int(iw * scale), int(ih * scale))
        original_image = pygame.transform.smoothscale(original_image, new_size)

    # ----------------------------
    # Create and Shuffle Puzzle Pieces
    # ----------------------------
    # Define where the complete puzzle should appear when solved.
    puzzle_start_pos = (50, 50)
    pieces = create_puzzle_pieces(original_image, GRID_ROWS, GRID_COLS, start_pos=puzzle_start_pos)
    shuffle_pieces(pieces, screen.get_rect())

    # ----------------------------
    # Variables to manage dragging
    # ----------------------------
    selected_piece = None
    offset_x, offset_y = 0, 0

    # ----------------------------
    # Main Game Loop
    # ----------------------------
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # When mouse button is pressed, check if a piece was clicked.
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Iterate in reverse order so that pieces drawn later (on top) get selected first.
                for piece in reversed(pieces):
                    if piece.rect.collidepoint(pos):
                        selected_piece = piece
                        # Calculate the offset between the mouse pos and the top-left corner of the piece.
                        offset_x = pos[0] - piece.rect.x
                        offset_y = pos[1] - piece.rect.y
                        piece.moving = True
                        # Bring the selected piece to the top (last drawn)
                        pieces.remove(piece)
                        pieces.append(piece)
                        break

            # When the mouse is moved, update the selected piece’s position.
            elif event.type == pygame.MOUSEMOTION:
                if selected_piece and selected_piece.moving:
                    new_pos = (event.pos[0] - offset_x, event.pos[1] - offset_y)
                    selected_piece.rect.topleft = new_pos

            # When the mouse button is released, try to snap the piece into place.
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if selected_piece:
                    selected_piece.moving = False
                    # Snap into place if close enough.
                    selected_piece.snap_to_place()
                    selected_piece = None

        # ----------------------------
        # Drawing
        # ----------------------------
        screen.fill((50, 50, 50))  # Dark gray background

        # Draw a faint outline for the solved puzzle area.
        puzzle_area = pygame.Rect(puzzle_start_pos, original_image.get_size())
        pygame.draw.rect(screen, (200, 200, 200), puzzle_area, 3)

        # Draw each piece.
        for piece in pieces:
            piece.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
