import pygame
from config import *
from config import TilemapManager
from model import AStarAlgorithm
from model import GeneticAlgorithm
from collections import deque
import math

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y, population_size=10, chromosome_length=10, mutation_rate=0.1):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = self.game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.image.load('assets/packman.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))

        # Initialize attributes
        self.direction = (0, 0)  # Initialize direction (dx, dy)
        self.tile_x = x
        self.tile_y = y
        self.rect.topleft = (self.tile_x * TILESIZE, self.tile_y * TILESIZE)
        self.moving = False
        self.target_x = self.tile_x * TILESIZE
        self.target_y = self.tile_y * TILESIZE
        self.collected_pellets = 0  # Track collected pellets
        self.speed = PLAYER_SPEED
        self.tilemap = TilemapManager.tilemap
        self.score = 0  # Attribute for SCORES

        self.path = []
        self.pathfinder = AStarAlgorithm(TilemapManager.tilemap)

        # Initialize the Genetic Algorithm for decision-making
        self.ga = GeneticAlgorithm(population_size, chromosome_length, mutation_rate, TilemapManager.tilemap)
        
        # Visited tiles tracker
        self.visited_tiles = set()  # Set to track visited tiles

    def move(self, dx=0, dy=0, use_ga=False, game=None):
        """
        Move the player, prioritizing GA for decision-making.
        Falls back to A* if GA doesn't produce a valid move.
        """
        if use_ga:
            if not game:
                raise ValueError("Game instance must be provided when using genetic algorithm.")

            # Find the nearest pellet using GA
            nearest_pellet = self.ga.get_target(game)
            if nearest_pellet:
                # Calculate A* path to the target
                a_star_path = self.pathfinder.find_path((self.tile_x, self.tile_y), nearest_pellet)
                if not a_star_path:
                    return  # No path found, exit early

                # Use GA to evolve and determine the next move
                best_chromosome = self.ga.evolve(game, a_star_path)
                if best_chromosome:
                    move_direction = best_chromosome[0]
                    dx, dy = self.get_move_direction(move_direction)
                    new_position = (self.tile_x + dx, self.tile_y + dy)

                    # Check for ghost proximity before executing the move
                    ghost_positions = [(enemy.tile_x, enemy.tile_y) for enemy in game.enemies]
                    if not self.is_near_enemy(new_position, ghost_positions):
                        # Validate the GA-suggested move
                        if self.pathfinder.is_walkable(new_position):
                            self._execute_move(dx, dy)
                            return  # Move executed successfully
                    # Else, continue without any debug output

                # Fallback to A*'s first step if GA fails
                next_position = a_star_path[0]
                dx, dy = next_position[0] - self.tile_x, next_position[1] - self.tile_y
                self._execute_move(dx, dy)
            else:
                # No valid target found for GA or A*
                return
        else:
            # Direct manual movement
            self._execute_move(dx, dy)


    def is_near_enemy(self, position, ghost_positions):
        """
        Check if the given position is near any enemy based on precomputed positions.
        """
        return any(abs(position[0] - ghost_x) + abs(position[1] - ghost_y) <= 1
                for ghost_x, ghost_y in ghost_positions)



    def _execute_move(self, dx, dy):
        """
        Execute the actual movement logic for the player.
        """
        if not self.moving:  # Only move if not already moving
            new_tile_x = self.tile_x + dx
            new_tile_y = self.tile_y + dy

            # Create a rect for the next position
            new_rect = pygame.Rect(new_tile_x * TILESIZE, new_tile_y * TILESIZE, TILESIZE, TILESIZE)

            # Check for collisions with blocks (walls)
            if any(new_rect.colliderect(block.rect) for block in self.game.blocks):
                print(f"Move blocked by wall at ({new_tile_x}, {new_tile_y})")
                return  # Stop the move if there is a collision

            # Proceed with movement
            self.moving = True
            self.direction = (dx, dy)  # Update direction
            self.target_x = new_tile_x * TILESIZE
            self.target_y = new_tile_y * TILESIZE

            # Update tile position immediately
            self.tile_x = new_tile_x
            self.tile_y = new_tile_y

            # Mark the tile as visited
            self.visited_tiles.add((self.tile_x, self.tile_y))

            tilemap = TilemapManager.tilemap

            # Handle teleporters
            if tilemap[self.tile_y][self.tile_x] == 'T':
                self.teleport()

            # Eat pellet if present
            if tilemap[self.tile_y][self.tile_x] == '.':
                self.eat_pellet()

    def get_move_direction(self, move):
        """
        Convert a move ('UP', 'DOWN', 'LEFT', 'RIGHT') into dx, dy direction.
        """
        if move == 'UP':
            return 0, -1
        elif move == 'DOWN':
            return 0, 1
        elif move == 'LEFT':
            return -1, 0
        elif move == 'RIGHT':
            return 1, 0
        return 0, 0

    def eat_pellet(self):
        tilemap = TilemapManager.tilemap
        if tilemap[self.tile_y][self.tile_x] == '.':
            tilemap[self.tile_y][self.tile_x] = ' '  # Replace pellet with empty space
            self.collected_pellets += 1
            self.score += 10  # Increment score
            TilemapManager.tilemap = tilemap

    def teleport(self):
        # Teleport logic: Move to the corresponding teleporter
        if (self.tile_x, self.tile_y) == (19, 9):  # Right teleporter
            self.tile_x, self.tile_y = 1, 9  # Move to left teleporter
        elif (self.tile_x, self.tile_y) == (1, 9):  # Left teleporter
            self.tile_x, self.tile_y = 19, 9  # Move to right teleporter

        # Update the rect position immediately to the new tile position
        self.rect.topleft = (self.tile_x * TILESIZE, self.tile_y * TILESIZE)
        self.moving = False  # Set moving to false immediately after teleportation

    def update(self, game):
        """
        Update the player's state. Handles movement logic.
        """
        if not self.moving:
            # Use the unified `move` method with GA and A*
            self.move(use_ga=True, game=game)
        else:
            # Smoothly move towards the target position
            dx = self.target_x - self.rect.x
            dy = self.target_y - self.rect.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance != 0:  # Prevent division by zero
                step_x = (dx / distance) * self.speed
                step_y = (dy / distance) * self.speed
                self.rect.x += step_x
                self.rect.y += step_y

                # Stop moving when the target is reached
                if abs(dx) <= self.speed and abs(dy) <= self.speed:
                    self.rect.x, self.rect.y = self.target_x, self.target_y
                    self.moving = False

class Blinky(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = self.game.all_sprites, self.game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.image.load('assets/blinky.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))  # Scale enemy to TILESIZE
        self.rect = self.image.get_rect()

        # Tile coordinates
        self.tile_x = x  # Tile coordinate X
        self.tile_y = y  # Tile coordinate Y

        # Set initial pixel position based on tile coordinates
        self.x = self.tile_x * TILESIZE
        self.y = self.tile_y * TILESIZE
        self.rect.topleft = (self.x, self.y)

        # Movement attributes
        self.is_moving = False
        self.speed = GHOST_SPEED
        self.last_move_time = pygame.time.get_ticks()

        self.target_tile = None  # Target tile for movement
        self.path = []  # Path to follow

    def calculate_goal(self):
        """Directly target the player's current tile."""
        player = self.game.player
        return player.tile_x, player.tile_y

    def move(self):
        """Move towards the target tile or follow the path."""
        current_time = pygame.time.get_ticks()

        # If actively moving towards a target tile
        if self.target_tile and self.is_moving:
            target_x, target_y = self.target_tile[0] * TILESIZE, self.target_tile[1] * TILESIZE
            dx, dy = target_x - self.x, target_y - self.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > 0:
                # Normalize the direction vector and move at the set speed
                step_x = (dx / distance) * self.speed
                step_y = (dy / distance) * self.speed
                self.x += step_x
                self.y += step_y
                self.rect.topleft = (round(self.x), round(self.y))

            # Snap to the target tile if close enough
            if abs(dx) < self.speed and abs(dy) < self.speed:
                self.x, self.y = target_x, target_y
                self.rect.topleft = (self.x, self.y)
                self.tile_x, self.tile_y = self.target_tile  # Update to the new tile position
                self.is_moving = False

        # If stationary, calculate a new path
        elif current_time - self.last_move_time > self.speed:
            if not self.is_moving and not self.path:
                start = (self.tile_x, self.tile_y)
                goal = self.calculate_goal()
                self.path = self.bfs(start, goal, tilemap)
                self.last_move_time = current_time

            if self.path:
                next_tile = self.path.pop(0)
                self.start_moving(next_tile)

    def get_position(self):
        """Return the current tile position."""
        return self.tile_x, self.tile_y

    def can_move_to(self, x, y, tilemap):
        """Check if the tile is walkable."""
        if x < 0 or x >= len(tilemap[0]) or y < 0 or y >= len(tilemap):
            return False  # Out of bounds
        if tilemap[y][x] == 'W':  # Wall tile
            return False
        return True

    def bfs(self, start, goal, tilemap):
        """Breadth-first search to find the shortest path."""
        queue = deque([start])
        visited = set([start])
        paths = {start: []}

        while queue:
            current = queue.popleft()
            if current == goal:
                return paths[current]

            x, y = current
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if (new_x, new_y) not in visited and self.can_move_to(new_x, new_y, tilemap):
                    queue.append((new_x, new_y))
                    visited.add((new_x, new_y))
                    paths[(new_x, new_y)] = paths[current] + [(new_x, new_y)]

        return []

    def start_moving(self, next_tile):
        """Set the next tile as the target for movement."""
        self.target_tile = next_tile
        self.is_moving = True


class Inky(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = self.game.all_sprites, self.game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.image.load('assets/inky.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))  # Scale enemy to TILESIZE
        self.rect = self.image.get_rect()

        # Tile coordinates
        self.tile_x = x
        self.tile_y = y

        # Set initial pixel position based on tile coordinates
        self.x = self.tile_x * TILESIZE
        self.y = self.tile_y * TILESIZE
        self.rect.topleft = (self.x, self.y)

        # Movement attributes
        self.is_moving = False
        self.speed = GHOST_SPEED
        self.last_move_time = pygame.time.get_ticks()

        self.target_tile = None  # Target tile for movement
        self.path = []  # Path to follow

    def calculate_goal(self):
        """Calculate the goal tile for Inky based on player's position and offset."""
        player = self.game.player
        radius = 2  # Offset distance from player
        offset_x = radius if player.direction[0] >= 0 else -radius
        offset_y = radius if player.direction[1] >= 0 else -radius
        inky_goal_tile = (player.tile_x + offset_x, player.tile_y + offset_y)

        # Clamp the goal to the tilemap boundaries
        inky_goal_tile = (
            max(0, min(len(tilemap[0]) - 1, inky_goal_tile[0])),
            max(0, min(len(tilemap) - 1, inky_goal_tile[1]))
        )
        return inky_goal_tile

    def move(self):
        """Move towards the target tile or follow the path."""
        current_time = pygame.time.get_ticks()

        if self.target_tile and self.is_moving:
            target_x, target_y = self.target_tile[0] * TILESIZE, self.target_tile[1] * TILESIZE
            dx, dy = target_x - self.x, target_y - self.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > 0:
                step_x = (dx / distance) * self.speed
                step_y = (dy / distance) * self.speed
                self.x += step_x
                self.y += step_y
                self.rect.topleft = (round(self.x), round(self.y))

            # Snap to the target tile if close enough
            if abs(dx) < self.speed and abs(dy) < self.speed:
                self.x, self.y = target_x, target_y
                self.rect.topleft = (self.x, self.y)
                self.tile_x, self.tile_y = self.target_tile
                self.is_moving = False

        elif current_time - self.last_move_time > self.speed:
            if not self.is_moving and not self.path:
                start = (self.tile_x, self.tile_y)
                goal = self.calculate_goal()
                self.path = self.dfs(start, goal, tilemap)
                self.last_move_time = current_time

            if self.path:
                next_tile = self.path.pop(0)
                self.start_moving(next_tile)

    def get_position(self):
        """Return the current tile position."""
        return self.tile_x, self.tile_y

    def can_move_to(self, x, y, tilemap):
        """Check if the tile is walkable."""
        if x < 0 or x >= len(tilemap[0]) or y < 0 or y >= len(tilemap):
            return False  # Out of bounds
        if tilemap[y][x] == 'W':  # Wall tile
            return False
        return True

    def dfs(self, start, goal, tilemap):
        """DFS for pathfinding."""
        stack = [(start, [])]
        visited = set()

        while stack:
            current, path = stack.pop()
            if current == goal:
                return path

            if current not in visited:
                visited.add(current)
                x, y = current

                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    new_x, new_y = x + dx, y + dy
                    if (new_x, new_y) not in visited and self.can_move_to(new_x, new_y, tilemap):
                        stack.append(((new_x, new_y), path + [(new_x, new_y)]))

        return []

    def start_moving(self, next_tile):
        """Set the next tile as the target for movement."""
        self.target_tile = next_tile
        self.is_moving = True


class Pinky(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = self.game.all_sprites, self.game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.image.load('assets/pinky.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))  # Scale enemy to TILESIZE
        self.rect = self.image.get_rect()

        # Tile coordinates
        self.tile_x = x
        self.tile_y = y

        # Set initial pixel position based on tile coordinates
        self.x = self.tile_x * TILESIZE
        self.y = self.tile_y * TILESIZE
        self.rect.topleft = (self.x, self.y)

        # Movement attributes
        self.is_moving = False
        self.speed = GHOST_SPEED
        self.last_move_time = pygame.time.get_ticks()

        self.target_tile = None  # Target tile for movement
        self.path = []  # Path to follow

    def calculate_goal(self):
        """Calculate the goal tile based on the player's position and direction."""
        player = self.game.player
        dx, dy = player.direction
        goal_x = player.tile_x + dx * 4
        goal_y = player.tile_y + dy * 4

        # Clamp the goal to the tilemap boundaries
        goal_x = max(0, min(len(tilemap[0]) - 1, goal_x))
        goal_y = max(0, min(len(tilemap) - 1, goal_y))

        return goal_x, goal_y

    def move(self):
        """Move towards the target tile or follow the path."""
        current_time = pygame.time.get_ticks()

        if self.target_tile and self.is_moving:
            target_x, target_y = self.target_tile[0] * TILESIZE, self.target_tile[1] * TILESIZE
            dx, dy = target_x - self.x, target_y - self.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > 0:
                step_x = (dx / distance) * self.speed
                step_y = (dy / distance) * self.speed
                self.x += step_x
                self.y += step_y
                self.rect.topleft = (round(self.x), round(self.y))

            # Snap to the target tile if close enough
            if abs(dx) < self.speed and abs(dy) < self.speed:
                self.x, self.y = target_x, target_y
                self.rect.topleft = (self.x, self.y)
                self.tile_x, self.tile_y = self.target_tile
                self.is_moving = False

        elif current_time - self.last_move_time > self.speed:
            if not self.is_moving and not self.path:
                start = (self.tile_x, self.tile_y)
                goal = self.calculate_goal()
                self.path = self.bfs(start, goal, tilemap)
                self.last_move_time = current_time

            if self.path:
                next_tile = self.path.pop(0)
                self.start_moving(next_tile)

    def get_position(self):
        """Return the current tile position."""
        return self.tile_x, self.tile_y

    def can_move_to(self, x, y, tilemap):
        """Check if the tile is walkable."""
        if x < 0 or x >= len(tilemap[0]) or y < 0 or y >= len(tilemap):
            return False  # Out of bounds
        if tilemap[y][x] == 'W':  # Wall tile
            return False
        return True

    def bfs(self, start, goal, tilemap):
        """Breadth-First Search for pathfinding."""
        queue = deque([start])
        visited = set([start])
        paths = {start: []}  # Store the path to each tile

        while queue:
            current = queue.popleft()
            if current == goal:
                return paths[current]

            x, y = current
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if (new_x, new_y) not in visited and self.can_move_to(new_x, new_y, tilemap):
                    queue.append((new_x, new_y))
                    visited.add((new_x, new_y))
                    paths[(new_x, new_y)] = paths[current] + [(new_x, new_y)]

        return []  # No path found

    def start_moving(self, next_tile):
        """Set the next tile as the target for movement."""
        self.target_tile = next_tile
        self.is_moving = True



class Clyde(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = self.game.all_sprites, self.game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.image.load('assets/clyde.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILESIZE, TILESIZE))  # Scale enemy to TILESIZE
        self.rect = self.image.get_rect()

        # Tile coordinates
        self.tile_x = x
        self.tile_y = y

        # Set initial pixel position based on tile coordinates
        self.x = self.tile_x * TILESIZE
        self.y = self.tile_y * TILESIZE
        self.rect.topleft = (self.x, self.y)

        # Movement attributes
        self.is_moving = False
        self.speed = GHOST_SPEED
        self.last_move_time = pygame.time.get_ticks()

        self.target_tile = None  # Target tile Clyde is moving towards
        self.path = []  # Path to follow

    def move(self):
        """Move Clyde towards the target tile."""
        current_time = pygame.time.get_ticks()

        if self.target_tile and self.is_moving:
            target_x, target_y = self.target_tile[0] * TILESIZE, self.target_tile[1] * TILESIZE
            dx, dy = target_x - self.x, target_y - self.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > 0:
                step_x = (dx / distance) * self.speed
                step_y = (dy / distance) * self.speed
                self.x += step_x
                self.y += step_y
                self.rect.topleft = (round(self.x), round(self.y))

            # Snap to the target tile if close enough
            if abs(dx) < self.speed and abs(dy) < self.speed:
                self.x, self.y = target_x, target_y
                self.rect.topleft = (self.x, self.y)
                self.tile_x, self.tile_y = self.target_tile
                self.is_moving = False

        elif current_time - self.last_move_time > self.speed:
            if not self.is_moving and not self.path:
                start = (self.tile_x, self.tile_y)
                goal = (self.game.player.tile_x, self.game.player.tile_y)
                self.path = self.dfs(start, goal, tilemap)
                self.last_move_time = current_time

            if self.path:
                next_tile = self.path.pop(0)
                self.start_moving(next_tile)

    def get_position(self):
        """Return the current tile position."""
        return self.tile_x, self.tile_y

    def can_move_to(self, x, y, tilemap):
        """Check if the tile is walkable."""
        if x < 0 or x >= len(tilemap[0]) or y < 0 or y >= len(tilemap):
            return False  # Out of bounds
        if tilemap[y][x] == 'W':  # Wall tile
            return False
        return True

    def dfs(self, start, goal, tilemap):
        """Depth-First Search for pathfinding."""
        stack = [(start, [])]
        visited = set()

        while stack:
            current, path = stack.pop()
            if current == goal:
                return path

            if current not in visited:
                visited.add(current)
                x, y = current

                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    new_x, new_y = x + dx, y + dy
                    if self.can_move_to(new_x, new_y, tilemap):
                        stack.append(((new_x, new_y), path + [(new_x, new_y)]))

        return []  # Return empty path if no valid path is found

    def start_moving(self, next_tile):
        """Set the next tile as the target for movement."""
        self.target_tile = next_tile
        self.is_moving = True



class Block(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCK_LAYER
        self.groups = self.game.all_sprites, self.game.blocks
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(BLUE)  # Blue blocks
        self.rect = self.image.get_rect()
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.rect.topleft = (self.x, self.y)

class Pellet(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self.groups = game.all_sprites, game.pellets
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.image = pygame.Surface((TILESIZE // 2, TILESIZE // 2))
        self.image.fill(WHITE)  # White pellets
        self.rect = self.image.get_rect()
        self.x = x * TILESIZE + TILESIZE // 4
        self.y = y * TILESIZE + TILESIZE // 4
        self.rect.topleft = (self.x, self.y)

class Ground(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()  # Not adding to any sprite group here
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(WHITE)  # Color for the ground
        self.rect = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))

    def update(self):
        pass  # No update needed for ground tiles
    
class Button:
    def __init__(self, x, y, width, height, text, font, color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        text_obj = self.font.render(self.text, True, self.text_color)
        text_rect = text_obj.get_rect(center=self.rect.center)
        surface.blit(text_obj, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)