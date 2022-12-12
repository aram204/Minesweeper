import itertools
import random
from copy import deepcopy

class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells) != 0 and len(self.cells) == self.count:
            return self.cells
        return None

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if len(self.cells) != 0 and self.count <= 0:
            return self.cells
        return None

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if self.cells and cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if self.cells and cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def get_neighbours(self, cell):
        neighbours_set = set()
        up = cell[0] - 1
        down = cell[0] + 1
        left = cell[1] - 1
        right = cell[1] + 1

        if cell[0] == 0:
            up = cell[0]
        elif cell[0] == self.height - 1:
            down = self.height - 1

        if cell[1] == 0:
            left = cell[1]
        elif cell[1] == self.width - 1:
            right = self.width - 1

        for row in range(up, down + 1):
            for col in range(left, right + 1):
                if (row, col) in self.safes:
                    continue
                neighbours_set.add((row, col))

        return neighbours_set

    def update_with_new_sentence(self):
        changed_things = 0
        for sent in self.knowledge:
            mines = sent.known_mines()
            safes = sent.known_safes()
            if mines is not None:
                for mine in deepcopy(mines):
                    self.mark_mine(mine)
                    changed_things += 1
            if safes is not None:
                for safe in deepcopy(safes):
                    self.mark_safe(safe)
                    changed_things += 1
        if changed_things > 0:
            self.update_with_new_sentence()

    def get_subset_knowledge(self):
        changed_things = 0
        new_knowledge = []
        for sent_1 in self.knowledge:
            for sent_2 in self.knowledge:
                cells_1 = sent_1.cells
                cells_2 = sent_2.cells
                count_1 = sent_1.count
                count_2 = sent_2.count
                if cells_1 != cells_2 and len(cells_1) != 0 and len(cells_2) != 0:
                    if cells_1.issubset(cells_2):
                        new_sent = Sentence(cells_2 - cells_1, count_2 - count_1)
                        new_knowledge = [sent if sent.cells != cells_2 else new_sent for sent in self.knowledge]
                        changed_things += 1
                    if cells_2.issubset(cells_1):
                        new_sent = Sentence(cells_1 - cells_2, count_1 - count_2)
                        new_knowledge = [sent if sent.cells != cells_1 else new_sent for sent in self.knowledge]
                        changed_things += 1
        if changed_things > 0:
            self.knowledge = new_knowledge

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        self.moves_made.add(cell)
        self.mark_safe(cell)
        neighbours = self.get_neighbours(cell)
        sentence = Sentence(neighbours, count)
        self.knowledge.append(sentence)
        self.update_with_new_sentence()
        self.get_subset_knowledge()

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.
        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        for move in self.safes:
            if move not in self.moves_made:
                return move

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        all_possible_cells = []
        for i in range(8):
            for j in range(8):
                if (i, j) not in self.moves_made and (i, j) not in self.mines:
                    all_possible_cells.append((i, j))
        if all_possible_cells:
            return random.choice(all_possible_cells)
        else:
            return None