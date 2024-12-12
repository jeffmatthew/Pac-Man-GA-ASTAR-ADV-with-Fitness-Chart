import heapq
import random
import matplotlib.pyplot as pl

class GeneticAlgorithm:
    def __init__(self, population_size, chromosome_length, mutation_rate, tilemap, adversarial_algorithm=None):
        """
        Initialize the Genetic Algorithm with parameters.
        """
        self.population_size = population_size
        self.chromosome_length = chromosome_length
        self.mutation_rate = mutation_rate
        self.tilemap = tilemap
        self.population = self.initialize_population()
        self.pathfinder = AStarAlgorithm(tilemap)
        self.adversarial_algorithm = adversarial_algorithm  # Optional: Pass in the AdversarialAlgorithm
        self.fitness_history = []  # Track max fitness of each generation

    def initialize_population(self):
        """
        Generate an initial population of random chromosomes (move sequences).
        """
        moves = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        return [[random.choice(moves) for _ in range(self.chromosome_length)]
                for _ in range(self.population_size)]

    def evaluate_fitness(self, game, chromosome, a_star_path, ghost_positions):
        if self.adversarial_algorithm:
            # Use the AdversarialAlgorithm's fitness evaluation instead
            return self.adversarial_algorithm.evaluate_fitness(game, chromosome, a_star_path, ghost_positions)
        else:
            # Fallback to the existing fitness evaluation logic if no AdversarialAlgorithm is provided
            return self.evaluate_fitness_without_adversarial(game, chromosome, a_star_path)

    def evaluate_fitness_without_adversarial(self, game, chromosome, a_star_path):
        """
        Evaluate the fitness without the adversarial component (used if AdversarialAlgorithm is not passed).
        """
        score = 0
        position = (game.player.tile_x, game.player.tile_y)
        visited = set()
        ghost_positions = [(enemy.tile_x, enemy.tile_y) for enemy in game.enemies]

        # Traverse each move in the chromosome
        for move in chromosome:
            new_position = self.simulate_move(position, move, game)

            # Penalize revisiting the same tile
            if new_position in visited:
                score -= 500  # Penalty for backtracking (revisiting)
            else:
                visited.add(new_position)
                # Reward for collecting pellets
                if self.tilemap[new_position[1]][new_position[0]] == '.':
                    score += 2500  # Pellet found, reward for it
                # Penalize for being near an enemy (ghost)
                if self.is_near_enemy(new_position, ghost_positions):
                    score -= 1000

            position = new_position

        # Reward for following A* path closely
        score += self.follow_a_star_path(a_star_path, chromosome, (game.player.tile_x, game.player.tile_y))

        return score

    def follow_a_star_path(self, a_star_path, chromosome, initial_position):
        """
        Reward the chromosome for following the A* path closely.
        """
        score = 0
        position = initial_position
        path_index = 0

        for move in chromosome:
            if path_index < len(a_star_path):
                next_position = a_star_path[path_index]
                direction_to_next = self.get_direction(position, next_position)

                if move == direction_to_next:
                    score += 100
                    position = next_position
                    path_index += 1
                else:
                    score -= 50
            else:
                score -= 20

        return score

    def get_direction(self, start, end):
        """
        Get the direction of movement based on start and end positions.
        """
        if not end:
            return None
        dx, dy = end[0] - start[0], end[1] - start[1]
        if dx == 1:
            return 'RIGHT'
        elif dx == -1:
            return 'LEFT'
        elif dy == 1:
            return 'DOWN'
        elif dy == -1:
            return 'UP'
        return None

    def simulate_move(self, position, move, game):
        """
        Simulate a move and return the new position if valid, otherwise return the original position.
        """
        x, y = position
        if move == 'UP':
            y -= 1
        elif move == 'DOWN':
            y += 1
        elif move == 'LEFT':
            x -= 1
        elif move == 'RIGHT':
            x += 1
        
        if (
            0 <= x < len(self.tilemap[0]) and
            0 <= y < len(self.tilemap) and
            self.tilemap[y][x] != 'W'
        ):
            return x, y
        return position

    def is_near_enemy(self, position, ghost_positions):
        """
        Check if the given position is near any enemy based on precomputed positions.
        """
        return any(abs(position[0] - ghost_x) + abs(position[1] - ghost_y) <= 1
                for ghost_x, ghost_y in ghost_positions)


    def evolve(self, game, a_star_path):
        start = (game.player.tile_x, game.player.tile_y)
        target = self.get_target(game)  # Get the next pellet or goal
        if target is None:
            return random.choice(self.population)  # No target, return any chromosome

        a_star_path = self.pathfinder.find_path(start, target)
        
        fitness_scores = [
            self.evaluate_fitness(game, chromosome, a_star_path, [(enemy.tile_x, enemy.tile_y) for enemy in game.enemies])
            for chromosome in self.population
        ]

        # Track the best fitness score for the current generation
        self.fitness_history.append(max(fitness_scores))
        print(f"Generation {len(self.fitness_history)} max fitness: {fitness_scores}")
        selected = self.select_population(self.population, fitness_scores)
        
        new_population = []
        while len(new_population) < self.population_size:
            parent1, parent2 = random.sample(selected, 2)
            child1, child2 = self.crossover(parent1, parent2)
            new_population.append(self.mutate(child1))
            if len(new_population) < self.population_size:
                new_population.append(self.mutate(child2))
        
        self.population = new_population
        best_chromosome = self.get_best_chromosome(fitness_scores)
        
        return best_chromosome

    def get_target(self, game):
        """
        Determine the nearest pellet for Pacman using the heuristic function.
        """
        start = (game.player.tile_x, game.player.tile_y)  # Current position of Pacman
        nearest_pellet = None
        min_distance = float('inf')

        for y, row in enumerate(self.tilemap):
            for x, tile in enumerate(row):
                if tile == '.':  # Pellet tile
                    distance = self.pathfinder.heuristic(start, (x, y))  # Use AStar's heuristic
                    if distance < min_distance:
                        min_distance = distance
                        nearest_pellet = (x, y)

        return nearest_pellet


    def select_population(self, population, fitness_scores):
        """
        Select a subset of the population based on their fitness scores using roulette selection.
        """
        total_fitness = sum(max(score, 0) for score in fitness_scores)
        if total_fitness == 0:
            return random.sample(population, len(population) // 2)
        probabilities = [max(score, 0) / total_fitness for score in fitness_scores]
        return random.choices(population, weights=probabilities, k=len(population) // 2)

    def crossover(self, parent1, parent2):
        """
        Perform single-point crossover between two parents.
        """
        split = random.randint(1, self.chromosome_length - 1)
        return parent1[:split] + parent2[split:], parent2[:split] + parent1[split:]

    def mutate(self, chromosome):
        moves = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        for i in range(len(chromosome)):
            if random.random() < self.mutation_rate:
                chromosome[i] = random.choice(moves)
        return chromosome

    def get_best_chromosome(self, fitness_scores):
        """
        Return the chromosome with the highest fitness score.
        """
        max_index = fitness_scores.index(max(fitness_scores))
        return self.population[max_index]


class AStarAlgorithm:
    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def heuristic(self, a, b):
        distance = abs(a[0] - b[0]) + abs(a[1] - b[1])
        # print(f"Heuristic from {a} to {b}: {distance}")  # Debugging Heuristic Calculation
        return distance

    def is_walkable(self, position):
        """
        Check if a given position is valid (not a wall or out of bounds).
        """
        x, y = position
        if 0 <= x < len(self.tilemap[0]) and 0 <= y < len(self.tilemap) and self.tilemap[y][x] != 'W':
            return True
        return False

    def find_path(self, start, goal, blocked_positions=None):
        if blocked_positions is None:
            blocked_positions = []
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                return self.reconstruct_path(came_from, current)
            for dx, dy in self.directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if not self.is_walkable(neighbor) or neighbor in blocked_positions:
                    continue
                tentative_g_score = g_score[current] + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))


            # # Debugging each iteration
            # print(f"Open Set: {open_set}")
            # print(f"Visited: {came_from}")
        return []

    def reconstruct_path(self, came_from, current):
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()
        # print(f"Reconstructed Path: {path}")  # Debugging Path
        return path
    

class AdversarialAlgorithm:
    def __init__(self, game, tilemap, genetic_algorithm, a_star_pathfinder):
        """
        Initialize the Adversarial Algorithm with necessary components.
        """
        self.game = game
        self.tilemap = tilemap
        self.genetic_algorithm = genetic_algorithm  # Reference to the Genetic Algorithm
        self.a_star_pathfinder = a_star_pathfinder  # Reference to the A* Pathfinding Algorithm

    def calculate_avoidance_path(self, start, target, ghost_positions):
        """
        Recalculate the path while avoiding ghosts. The pathfinder should try to
        avoid paths that are too close to the ghosts.
        """
        blocked_positions = set(ghost_positions)  # Mark ghost positions as blocked
        return self.a_star_pathfinder.find_path(start, target, blocked_positions)

    def evaluate_fitness(self, game, chromosome, a_star_path, ghost_positions):
        """
        Evaluates the fitness of a chromosome based on its ability to collect pellets,
        follow the A* path, and avoid ghosts.
        """
        score = 0
        position = (game.player.tile_x, game.player.tile_y)
        visited = set()

        for move in chromosome:
            new_position = self.genetic_algorithm.simulate_move(position, move, game)

            # Penalize revisiting the same tile
            if new_position in visited:
                score -= 500
            else:
                visited.add(new_position)

                # Reward for collecting pellets
                if self.tilemap[new_position[1]][new_position[0]] == '.':
                    score += 2500

                # Penalize if close to a ghost
                if self.is_near_enemy(new_position, ghost_positions):
                    score -= 1000

            position = new_position

        # Reward for staying on the A* path
        score += self.genetic_algorithm.follow_a_star_path(a_star_path, chromosome, (game.player.tile_x, game.player.tile_y))

        return score

    def is_near_enemy(self, position, ghost_positions):
        """
        Check if the given position is near any enemy (ghost).
        """
        return any(abs(position[0] - ghost_x) + abs(position[1] - ghost_y) <= 1
                for ghost_x, ghost_y in ghost_positions)

    def evolve(self, game, a_star_path):
        """
        Evolve the population while considering adversarial factors (ghost avoidance).
        """
        start = (game.player.tile_x, game.player.tile_y)
        target = self.genetic_algorithm.get_target(game)  # Next pellet/goal

        if target is None:
            return random.choice(self.genetic_algorithm.population)  # No target, return any chromosome

        # Avoidance path considering ghost positions
        ghost_positions = [(enemy.tile_x, enemy.tile_y) for enemy in game.enemies]
        a_star_path = self.calculate_avoidance_path(start, target, ghost_positions)

        # Evaluate fitness and evolve population
        fitness_scores = [self.evaluate_fitness(game, chromosome, a_star_path, ghost_positions) for chromosome in self.genetic_algorithm.population]
        selected = self.genetic_algorithm.select_population(self.genetic_algorithm.population, fitness_scores)

        new_population = []
        while len(new_population) < self.genetic_algorithm.population_size:
            parent1, parent2 = random.sample(selected, 2)
            child1, child2 = self.genetic_algorithm.crossover(parent1, parent2)
            new_population.append(self.genetic_algorithm.mutate(child1))
            if len(new_population) < self.genetic_algorithm.population_size:
                new_population.append(self.genetic_algorithm.mutate(child2))

        self.genetic_algorithm.population = new_population
        best_chromosome = self.genetic_algorithm.get_best_chromosome(fitness_scores)
        
        return best_chromosome


