# main.py
import pygame
from config import *
from config import TilemapManager
from object import *
import sys
import time
import matplotlib.pyplot as plt


# Game Class to encapsulate all game logic
class Game:
    def __init__(self):
        pygame.init()
        
        # Set up the screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man Game")
        
        # Clock to control the frame rate
        self.clock = pygame.time.Clock()
        
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.pellets = pygame.sprite.Group()

        self.levels = 0
        self.current_level = 1
        self.pellet_count = 0
        self.score = 0 # score for each level
        self.total_score = 0 # score total from each game
        self.start_time = time.time()
        self.total_elapsed_time = 0
        self.collision_cooldown_duration = 1.0  # 1 second cooldown
        self.last_collision_time = 0  # Last time a collision occurred

        self.tilemap = TilemapManager.tilemap
        self.a_star = AStarAlgorithm(self.tilemap)  # Initialize AStarAlgorithm
        self.ga = GeneticAlgorithm(
            population_size=100, chromosome_length=50, mutation_rate=0.1, tilemap=self.tilemap
        )

    def reset_tilemap(self):
        """Restore the tilemap to its original state."""
        global tilemap
        tilemap = [list(row) for row in original_tilemap]
        TilemapManager.tilemap = tilemap

    def count_total_pellets(self):
        total_pellets = 0
        for row in tilemap:
            total_pellets += row.count('.')  # Count pellets represented by '.'
        return total_pellets

    # Initialize game elements
    def init_game(self):
        self.reset_tilemap()
        self.all_sprites.empty()
        self.enemies.empty()
        self.blocks.empty()
        self.pellets.empty()
        self.score = 0
        self.start_time = time.time()

        self.pellet_count = self.count_total_pellets()  # Get the total pellet count
        print(f"Total pellets: {self.pellet_count}")  # Print total for verification

        for row_index, row in enumerate(tilemap):
            for col_index, tile in enumerate(row):
                if tile == 'W':
                    Block(self, col_index, row_index)  # Walls/Blocks
                elif tile == 'P':
                    self.player = Player(self, col_index, row_index)  # Pac-Man Player
                elif tile == 'R':
                    self.blinky = Blinky(self, col_index, row_index)  # Red Ghost Enemy
                    self.enemies.add(self.blinky)
                elif tile == 'L' and self.difficulty in ['medium' ,'hard', 'very_hard']:
                    self.pinky = Pinky(self, col_index, row_index)  # Pink Ghost Enemy
                    self.enemies.add(self.pinky)
                elif tile == 'I' and self.difficulty in ['hard', 'very_hard']:
                    self.inky = Inky(self, col_index, row_index)  # Cyan Ghost Enemy
                    self.enemies.add(self.inky)
                elif tile == 'C' and self.difficulty == 'very_hard':
                    self.clyde = Clyde(self, col_index, row_index)  # Orange Ghost Enemy
                    self.enemies.add(self.clyde)
                elif tile == '.':
                    Pellet(self, col_index, row_index)  # Pellets
                elif tile == ' ':
                    Ground(self, col_index, row_index)  # Ground

        self.all_sprites.add(self.player)
        self.all_sprites.add(self.enemies)
        self.all_sprites.add(self.blocks)
        self.all_sprites.add(self.pellets)

    def new_level_screen(self):
        font_large = pygame.font.Font(None, 74)  # Font for the main level message
        font_small = pygame.font.Font(None, 36)  # Font for the score details
        
        # Fill screen with background color
        self.screen.fill(BLACK)
        
        # Draw the main "Level {n}" text
        self.draw_text(
            f"Level {self.current_level}", 
            font_large, 
            YELLOW, 
            self.screen, 
            SCREEN_WIDTH // 2, 
            SCREEN_HEIGHT // 2 - 100
        )
        
        # Display the debug-style level details
        level_score_text = f"Score for Level {self.current_level}: {self.score}"
        total_score_text = f"Total Score: {self.total_score}"

        self.draw_text(
            level_score_text, 
            font_small, 
            WHITE, 
            self.screen, 
            SCREEN_WIDTH // 2, 
            SCREEN_HEIGHT // 2 - 20
        )
        self.draw_text(
            total_score_text, 
            font_small, 
            WHITE, 
            self.screen, 
            SCREEN_WIDTH // 2, 
            SCREEN_HEIGHT // 2 + 20
        )

        # Update the display
        pygame.display.flip()
        
        # Pause for 2 seconds before starting the next level
        pygame.time.wait(2000)



    def draw_text(self, text, font, color, surface, x, y):
        """Helper function to draw text on screen."""
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect(center=(x, y))
        surface.blit(text_obj, text_rect)

        
    def intro_screen(self):
        font = pygame.font.Font(None, 74)
        message_font = pygame.font.Font(None, 50)
        button_font = pygame.font.Font(None, 36)
        input_font = pygame.font.Font(None, 36)
        
        # Input field setup
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 320, 200, 40)
        input_text = ''
        input_active = False
        placeholder_text = "Enter levels"

        # Create buttons for Easy and Hard modes
        easy_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50, 'Easy', button_font, GREEN, BLACK)
        medium_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 120, 200, 50, 'Medium', button_font, YELLOW, BLACK)
        hard_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 190, 200, 50, 'Hard', button_font, RED, BLACK)
        very_hard_button = Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 260, 200, 50, 'Very Hard', button_font, DARK_RED, BLACK)
        
        while True:
            self.screen.fill(BLACK)
            
            # Draw game title and instructions
            self.draw_text("PACK-GUY", font, YELLOW, self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
            self.draw_text("Please choose the difficulty of the game!", message_font, WHITE, self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)

            # Draw difficulty selection buttons
            easy_button.draw(self.screen)
            hard_button.draw(self.screen)
            medium_button.draw(self.screen)
            very_hard_button.draw(self.screen)

            # Draw the input box
            pygame.draw.rect(self.screen, WHITE, input_box, 2 if input_active else 1)
            if input_text:
                # Display user-entered text
                input_surface = input_font.render(input_text, True, WHITE)
            else:
                # Display placeholder text
                input_surface = input_font.render(placeholder_text, True, GRAY)
            self.screen.blit(input_surface, (input_box.x + 5, input_box.y + 5))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if the input box is clicked
                    if input_box.collidepoint(event.pos):
                        input_active = True  # Activate input box
                    else:
                        input_active = False  # Deactivate input box
                    
                    # Handle button clicks for difficulty
                    if event.button == 1:  # Left click
                        if easy_button.is_clicked(event.pos):
                            self.difficulty = 'easy'
                            return 'intro'
                        elif medium_button.is_clicked(event.pos):
                            self.difficulty = 'medium'
                            return 'intro'
                        elif hard_button.is_clicked(event.pos):
                            self.difficulty = 'hard'
                            return 'intro'
                        elif very_hard_button.is_clicked(event.pos):
                            self.difficulty = 'very_hard'
                            return 'intro'

                if event.type == pygame.KEYDOWN:
                    # Handle text input when input box is active
                    if input_active:
                        if event.key == pygame.K_RETURN:
                            try:
                                # Set the number of levels from input text
                                self.levels = max(1, int(input_text))  # Ensure at least 1 level
                                print(f"Number of levels set to: {self.levels}")
                            except ValueError:
                                print("Invalid level input, defaulting to 5 levels.")
                                self.levels = 5  # Default fallback
                            input_active = False
                            input_text = ''  # Clear input after submission
                        elif event.key == pygame.K_BACKSPACE:
                            input_text = input_text[:-1]  # Remove last character
                        else:
                            input_text += event.unicode  # Add new character to input text
                    else:
                        # Handle hotkeys only when input box is not active
                        if event.key == pygame.K_1:
                            self.difficulty = 'easy'
                            return 'intro'
                        elif event.key == pygame.K_2:
                            self.difficulty = 'medium'
                            return 'intro'
                        elif event.key == pygame.K_3:
                            self.difficulty = 'hard'
                            return 'intro'
                        elif event.key == pygame.K_4:
                            self.difficulty = 'very_hard'
                            return 'intro'

            pygame.display.flip()
            self.clock.tick(60)

    # Game Over Screen
    def game_over_screen(self, status, final_score, elapsed_time):

        font = pygame.font.Font(None, 74)
        score_font = pygame.font.Font(None, 36)
        button_font = pygame.font.Font(None, 50)

        # Define the Show Chart button rectangle
        show_chart_button = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 50)

        while True:
            self.screen.fill(BLACK)

            # Display the win or game over text
            if status == 'win':
                self.draw_text("YOU WIN!", font, GREEN, self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
                self.draw_text(f"Final Score: {final_score}", score_font, WHITE, self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                # Display the final time in seconds
                minutes, seconds = divmod(int(elapsed_time), 60)
                time_text = f"Total Time: {minutes}m {seconds}s"
                self.draw_text(time_text, score_font, WHITE, self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)

            # Draw Show Chart button
            pygame.draw.rect(self.screen, WHITE, show_chart_button)
            self.draw_text("Show Chart", button_font, BLACK, self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 125)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and show_chart_button.collidepoint(event.pos):
                        # Show the fitness chart
                        print("Show Chart button clicked!")  # Debugging log
                        self.plot_fitness_chart()
                        return 'restart'  # Return to intro screen after showing the chart

                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    # Treat pressing Enter as showing the chart
                    print("Enter pressed to show chart!")  # Debugging log
                    self.plot_fitness_chart()
                    return 'restart'  # Return to intro screen after showing the chart

            pygame.display.flip()
            self.clock.tick(60)  # Limit to 60 frames per second

    # Plot Fitness Chart Method
    def plot_fitness_chart(self):
        if hasattr(self.ga, "fitness_history") and self.ga.fitness_history:
            plt.figure(figsize=(10, 6))
            plt.plot(range(1, len(self.ga.fitness_history) + 1), self.ga.fitness_history, marker='o')
            plt.title('Fitness Over Generations')
            plt.xlabel('Generation')
            plt.ylabel('Fitness')
            plt.grid(True)
            plt.show()  # This will block execution until the chart window is closed
        else:
            print("No fitness history available to plot.")  # Debugging message


    # Main game loop
    def game_loop(self):
        self.init_game()
        self.total_score = 0
        self.start_time = time.time()  # Record the start time
        self.current_level = 1
        back_button = pygame.Rect(10, SCREEN_HEIGHT - 60, 100, 40)

        while self.current_level <= self.levels:
            self.new_level_screen()
            self.init_game()
            a_star_path = None
            level_start_time = time.time()

            while True:
                self.screen.fill(BLACK)
                self.all_sprites.update(self)  # Update all sprites
                self.all_sprites.draw(self.screen)  # Draw all sprites

             # Run genetic algorithm for each frame or at specific intervals
                if hasattr(self, 'ga'):
                    best_chromosome = self.ga.evolve(self, a_star_path)  # Ensure this runs

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1 and back_button.collidepoint(event.pos):
                            return False # Exit the game loop and return to intro screen    
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                        return False

                # Call each enemy's move method
                if hasattr(self, 'blinky'):
                    self.blinky.move()
                if hasattr(self, 'pinky'):
                    self.pinky.move()
                if hasattr(self, 'inky'):
                    self.inky.move()
                if hasattr(self, 'clyde'):
                    self.clyde.move()


                # Calculate elapsed time for the timer
                elapsed_time = int(time.time() - self.start_time)
                hours = elapsed_time // 3600
                minutes = (elapsed_time % 3600) // 60
                seconds = elapsed_time % 60
                timer_text = f"Time: {hours:02}:{minutes:02}:{seconds:02}"

                # Display the score on the screen
                font = pygame.font.Font(None, 36)
                self.draw_text(f"Score: {self.score}", font, WHITE, self.screen, SCREEN_WIDTH - 100, 30)
                self.draw_text(timer_text, font, WHITE, self.screen, SCREEN_WIDTH - 100, 60)

                # Draw the back button
                pygame.draw.rect(self.screen, WHITE, back_button)
                self.draw_text("Back", font, BLACK, self.screen, back_button.centerx, back_button.centery)

                # Handling collisions with enemies
                if pygame.sprite.spritecollideany(self.player, self.enemies):
                    elapsed_time = time.time() - self.start_time  # Calculate elapsed time
                    current_time = time.time()
                    # technically IFrames
                    if current_time - self.last_collision_time >=  self.collision_cooldown_duration:
                        self.score -= 500  # Deduct points on collision
                        self.last_collision_time = current_time  # Update last collision time

                # Update score and pellet count
                collected_pellets = pygame.sprite.spritecollide(self.player, self.pellets, True)
                if collected_pellets:
                    self.pellet_count -= len(collected_pellets)
                    self.score += len(collected_pellets) * 100  # Add collected pellets to score
                    # print(f"Collected pellets: {len(collected_pellets)}, Remaining pellets: {self.pellet_count}")

                # Check if level is completed
                if self.pellet_count <= 0:
                    # Update total score and print level stats
                    self.total_score += self.score
                    level_elapsed_time = time.time() - level_start_time
                    self.total_elapsed_time += level_elapsed_time

                    # Print level completion details to the terminal
                    print(f"Level {self.current_level} Completed!")
                    print(f"Score for Level {self.current_level}: {self.score}")
                    print(f"Total Score: {self.total_score}")
                    print(f"Time Taken for Level {self.current_level}: {level_elapsed_time:.2f} seconds")
                    print(f"Total Time of Game Session: {self.total_elapsed_time:.2f}")

                    self.new_level_screen()
                    # Move to the next level
                    self.score = 0  # Reset the level score for the next level
                    self.current_level += 1
                    break  # Break out of the inner loop to start the next level



                pygame.display.flip()
                self.clock.tick(FPS)

            # Calculate final elapsed time
        final_elapsed_time = self.total_elapsed_time

        # Game over screen
        self.game_over_screen('win', self.total_score, final_elapsed_time)

if __name__ == "__main__":
    game = Game()
    while True:
        result = game.intro_screen()  # Show intro screen for game setup
        if result == 'intro':  # Check if the game should start
            result = game.game_loop()  # Start the game loop
            if result == 'restart':
                continue  # Restart the game loop
            # If game loop ends, show game over screen
            result = game.game_over_screen('win', game.total_score, game.total_elapsed_time)
            if result == 'restart':  # Restart the game if the player clicks Show Chart
                continue
