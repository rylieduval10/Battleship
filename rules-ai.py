import random

class Ship: #represents a ship, has size, orientation, and location
    def __init__(self, size):
        self.size = size
        self.orientation = random.choice(["h", "v"])
        self.row, self.col = self.random_position()
        self.indexes = self.compute_indexes()

    def random_position(self):
        #randomizes postition of the ship
        if self.orientation == "h":
            row = random.randrange(0, 10)
            col = random.randrange(0, 11 - self.size)
        else:
            row = random.randrange(0, 11 - self.size)
            col = random.randrange(0, 10)
        return row, col

    def compute_indexes(self):
        if self.orientation == "h":
            return [self.row * 10 + self.col + i for i in range(self.size)]
        else:
            return [(self.row + i) * 10 + self.col for i in range(self.size)]
#represents a player 
class Player:  
    def __init__(self):
        self.ships = []
        self.search = ["U" for _ in range(100)]  # "u" = unknown
        self.place_ships([5, 4, 3, 3, 2])
        self.indexes = [idx for ship in self.ships for idx in ship.indexes]

    def place_ships(self, sizes):
        for size in sizes: 
            placed = False
            while not placed:
                ship = Ship(size)
                possible = True
                for i in ship.indexes:
                    if i >= 100:
                        possible = False
                        break
                    new_row = i // 10
                    new_col = i % 10
                    if ship.orientation == "h" and new_row != ship.row:
                        possible = False
                        break
                    if ship.orientation == "v" and new_col != ship.col:
                        possible = False
                        break
                    for other_ship in self.ships:
                        if i in other_ship.indexes:
                            possible = False
                            break
                if possible: 
                    self.ships.append(ship)
                    placed = True

    def show_ships(self):
        indexes = ["-" if i not in self.indexes else "X" for i in range(100)]
        for row in range(10):
            print(" ".join(indexes[row*10:(row+1)*10]))

class Game: 
    def __init__(self, human1, human2):
        self.human1 = human1
        self.human2 = human2
        self.player1 = Player()
        self.player2 = Player()
        self.player1_turn = True
        self.computer_turn = not self.human1
        self.over = False
        self.result = None

    def make_move(self, i):
        player = self.player1 if self.player1_turn else self.player2
        opponent = self.player2 if self.player1_turn else self.player1
        hit = False

        if i in opponent.indexes: 
            player.search[i] = "H"
            hit = True
            # checks if the ship is sunk
            for ship in opponent.ships:
                if all(player.search[idx] == "H" or player.search[idx] == "S" for idx in ship.indexes):
                    for idx in ship.indexes:
                        player.search[idx] = "S"
        else:
            player.search[i] = "M"

        # checks if the game is over
        game_over = all(player.search[i] != "U" for i in opponent.indexes)
        self.over = game_over
        if game_over:
            self.result = 1 if self.player1_turn else 2

        # change turns
        if not hit:
            self.player1_turn = not self.player1_turn
            if (self.human1 and not self.human2) or (not self.human1 and self.human1):
                self.computer_turn = not self.computer_turn

    def random_ai(self):
        player = self.player1 if self.player1_turn else self.player2
        unknown = [i for i, square in enumerate(player.search) if square == "U"]
        if unknown:
            self.make_move(random.choice(unknown))

    def basic_ai(self):
        player = self.player1 if self.player1_turn else self.player2
        search = player.search
        unknown = [i for i, square in enumerate(search) if square == "U"]
        hits = [i for i, square in enumerate(search) if square == "H"]

        unknown_with_neighboring_hits = []
        for u in unknown:
            neighbors = [u+1, u-1, u+10, u-10]
            if any(0 <= n < 100 and search[n] == "H" for n in neighbors):
                unknown_with_neighboring_hits.append(u)

        if unknown_with_neighboring_hits:
            self.make_move(random.choice(unknown_with_neighboring_hits))
            return

        self.random_ai()

    def get_remaining_ship_sizes(self, opponent, search):
        sunk_ship_sizes = []
        for ship in opponent.ships:
            if all(search[idx] == "S" for idx in ship.indexes):
                sunk_ship_sizes.append(ship.size)
        all_ship_sizes = [ship.size for ship in opponent.ships]
        remaining = list(all_ship_sizes)
        for size in sunk_ship_sizes:
            if size in remaining:
                remaining.remove(size)
        return remaining

    def probability_ai(self):
        player = self.player1 if self.player1_turn else self.player2
        opponent = self.player2 if self.player1_turn else self.player1
        search = player.search

        probability = [0 for _ in range(100)]
        remaining_ship_sizes = self.get_remaining_ship_sizes(opponent, search)
        if not remaining_ship_sizes:
            remaining_ship_sizes = [5, 4, 3, 3, 2]  # fallback

        for ship_size in remaining_ship_sizes:
            # horizontal
            for row in range(10):
                for col in range(11 - ship_size):
                    indexes = [row * 10 + col + i for i in range(ship_size)]
                    if all(search[idx] == "U" for idx in indexes):
                        for idx in indexes:
                            probability[idx] += 1
            # vertical
            for col in range(10):
                for row in range(11 - ship_size):
                    indexes = [(row + i) * 10 + col for i in range(ship_size)]
                    if all(search[idx] == "U" for idx in indexes):
                        for idx in indexes:
                            probability[idx] += 1

        max_prob = max(probability)
        candidates = [i for i, val in enumerate(probability) if val == max_prob and search[i] == "U"]
        if candidates:
            self.make_move(random.choice(candidates))
        else:
            self.random_ai()

    def target_mode_ai(self):
        player = self.player1 if self.player1_turn else self.player2
        search = player.search

        # find all unsunk hits
        hits = [i for i, v in enumerate(search) if v == "H"]
        if not hits:
            self.probability_ai()
            return

        # group hits into connected components (ships being targeted)
        def get_neighbors(idx):
            row, col = divmod(idx, 10)
            neighbors = []
            if row > 0: neighbors.append(idx - 10)
            if row < 9: neighbors.append(idx + 10)
            if col > 0: neighbors.append(idx - 1)
            if col < 9: neighbors.append(idx + 1)
            return neighbors

        # find connected hits (for multi-hit ships)
        visited = set()
        groups = []

        for idx in hits:
            if idx in visited:
                continue
            # bfs to find all connected hits
            queue = [idx]
            group = []
            while queue:
                current = queue.pop()
                if current in visited:
                    continue
                visited.add(current)
                group.append(current)
                for n in get_neighbors(current):
                    if n in hits and n not in visited:
                        queue.append(n)
            groups.append(group)

        # for each group, try to finish the ship
        for group in groups:
            if len(group) > 1:
                # determine orientation
                rows = [g // 10 for g in group]
                cols = [g % 10 for g in group]
                if len(set(rows)) == 1:  # horizontal
                    row = rows[0]
                    min_col = min(cols)
                    max_col = max(cols)
                    left = row * 10 + min_col - 1 if min_col > 0 else None
                    right = row * 10 + max_col + 1 if max_col < 9 else None
                    candidates = []
                    if left is not None and search[left] == "U":
                        candidates.append(left)
                    if right is not None and search[right] == "U":
                        candidates.append(right)
                    if candidates:
                        self.make_move(random.choice(candidates))
                        return
                elif len(set(cols)) == 1:  # vertical
                    col = cols[0]
                    min_row = min(rows)
                    max_row = max(rows)
                    up = (min_row - 1) * 10 + col if min_row > 0 else None
                    down = (max_row + 1) * 10 + col if max_row < 9 else None
                    candidates = []
                    if up is not None and search[up] == "U":
                        candidates.append(up)
                    if down is not None and search[down] == "U":
                        candidates.append(down)
                    if candidates:
                        self.make_move(random.choice(candidates))
                        return
            for idx in group:
                for n in get_neighbors(idx):
                    if search[n] == "U":
                        self.make_move(n)
                        return

        # fallback to hunt mode
        self.probability_ai()

