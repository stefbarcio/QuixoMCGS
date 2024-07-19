from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum
import numpy as np
from MCTS import Node
from random import choice
from time import sleep


WINNING_COMBS = [17318416, 8659208, 4329604, 2164802, 1082401, 32505856, 1015808, 31744, 992, 31, 17043521, 1118480]
FRONTIER_INDEXES = [0, 1, 2, 3, 4, 5, 9, 10, 14, 15, 19, 20,21,22,23,24]
UPPER_FRONTIER = [0,1,2,3,4]
LEFT_FRONTIER = [0,5,10,15,20]
RIGHT_FRONTIER = [4,9,14,19,24]
LOWER_FRONTIER = [20,21,22,23,24]




class Move(Enum):
    '''
    Selects where you want to place the taken piece. The rest of the pieces are shifted
    '''
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3

class Player(ABC):
    def __init__(self) -> None:
        '''You can change this for your player if you need to handle state/have memory'''
        pass

    @abstractmethod
    def make_move(self, g, board, player) -> int:
        '''
        The game accepts coordinates of the type (X, Y). X goes from left to right, while Y goes from top to bottom, as in 2D graphics.
        Thus, the coordinates that this method returns shall be in the (X, Y) format.

        game: the Quixo game. You can use it to overrboarde the current game with yours, but everything is evaluated by the main game
        return values: this method shall return a tuple of X,Y positions and a move among TOP, BOTTOM, LEFT and RIGHT
        '''
        pass


class Game(object):
    def __init__(self) -> None:
        self.current_board = State(0)
        self.current_player = "O"
        self._board = np.ones((5, 5), dtype=np.uint8) * -1
        self.current_player_idx = 1

    def print(self):
      '''Prints the board. -1 are neutral pieces, 0 are pieces of player 0, 1 pieces of player 1'''
      print(self._board)

    def get_board(self) -> np.ndarray:
        '''
        Returns the board
        '''

        return deepcopy(self.current_board.board)


    def set_board(self, board):
        self.current_board = State(board)

    def get_current_player(self) -> int:
        '''
        Returns the current player
        '''
        return deepcopy(self.current_player_boardx)

    def check_winner(self) -> int:
      '''Check the winner. Returns the player ID of the winner if any, otherwise returns -1'''
      # for each row
      for x in range(self._board.shape[0]):
          # if a player has completed an entire row
          if self._board[x, 0] != -1 and all(self._board[x, :] == self._board[x, 0]):
              # return the relative id
              return self._board[x, 0]
      # for each column
      for y in range(self._board.shape[1]):
          # if a player has completed an entire column
          if self._board[0, y] != -1 and all(self._board[:, y] == self._board[0, y]):
              # return the relative id
              return self._board[0, y]
      # if a player has completed the principal diagonal
      if self._board[0, 0] != -1 and all(
          [self._board[x, x]
              for x in range(self._board.shape[0])] == self._board[0, 0]
      ):
          # return the relative id
          return self._board[0, 0]
      # if a player has completed the secondary diagonal
      if self._board[0, -1] != -1 and all(
          [self._board[x, -(x + 1)]
            for x in range(self._board.shape[0])] == self._board[0, -1]
      ):
          # return the relative id
          return self._board[0, -1]
      return -1



### PLAY FUNCTIONS
    
    def play(self, player1: Player, player2: Player) -> int:
        '''Play the game. Returns the winning player'''
        players = [player1, player2]
        winner = -1
        while winner < 0:
            self.current_player_idx += 1
            self.current_player_idx %= len(players)
            ok = False
            while not ok:
                from_pos, slide = players[self.current_player_idx].make_move(
                    self)
                ok = self.__move(from_pos, slide, self.current_player_idx)
            self.print()
            print()
            winner = self.check_winner()
        return winner

    def __move(self, from_pos: tuple[int, int], slide: Move, player_id: int) -> bool:
            '''Perform a move'''
            if player_id > 2:
                return False
            # Oh God, Numpy arrays
            prev_value = deepcopy(self._board[(from_pos[1], from_pos[0])])
            acceptable = self.__take((from_pos[1], from_pos[0]), player_id)
            if acceptable:
                acceptable = self.__slide((from_pos[1], from_pos[0]), slide)
                if not acceptable:
                    self._board[(from_pos[1], from_pos[0])] = deepcopy(prev_value)
            return acceptable

    def __take(self, from_pos: tuple[int, int], player_id: int) -> bool:
        '''Take piece'''
        # acceptable only if in border
        acceptable: bool = (
            # check if it is in the first row
            (from_pos[0] == 0 and from_pos[1] < 5)
            # check if it is in the last row
            or (from_pos[0] == 4 and from_pos[1] < 5)
            # check if it is in the first column
            or (from_pos[1] == 0 and from_pos[0] < 5)
            # check if it is in the last column
            or (from_pos[1] == 4 and from_pos[0] < 5)
            # and check if the piece can be moved by the current player
        ) and (self._board[from_pos] < 0 or self._board[from_pos] == player_id)
        if acceptable:
            self._board[from_pos] = player_id
        return acceptable

    def __slide(self, from_pos: tuple[int, int], slide: Move) -> bool:
        '''Slide the other pieces'''
        # define the corners
        SIDES = [(0, 0), (0, 4), (4, 0), (4, 4)]
        # if the piece position is not in a corner
        if from_pos not in SIDES:
            # if it is at the TOP, it can be moved down, left or right
            acceptable_top: bool = from_pos[0] == 0 and (
                slide == Move.BOTTOM or slide == Move.LEFT or slide == Move.RIGHT
            )
            # if it is at the BOTTOM, it can be moved up, left or right
            acceptable_bottom: bool = from_pos[0] == 4 and (
                slide == Move.TOP or slide == Move.LEFT or slide == Move.RIGHT
            )
            # if it is on the LEFT, it can be moved up, down or right
            acceptable_left: bool = from_pos[1] == 0 and (
                slide == Move.BOTTOM or slide == Move.TOP or slide == Move.RIGHT
            )
            # if it is on the RIGHT, it can be moved up, down or left
            acceptable_right: bool = from_pos[1] == 4 and (
                slide == Move.BOTTOM or slide == Move.TOP or slide == Move.LEFT
            )
        # if the piece position is in a corner
        else:
            # if it is in the upper left corner, it can be moved to the right and down
            acceptable_top: bool = from_pos == (0, 0) and (
                slide == Move.BOTTOM or slide == Move.RIGHT)
            # if it is in the lower left corner, it can be moved to the right and up
            acceptable_left: bool = from_pos == (4, 0) and (
                slide == Move.TOP or slide == Move.RIGHT)
            # if it is in the upper right corner, it can be moved to the left and down
            acceptable_right: bool = from_pos == (0, 4) and (
                slide == Move.BOTTOM or slide == Move.LEFT)
            # if it is in the lower right corner, it can be moved to the left and up
            acceptable_bottom: bool = from_pos == (4, 4) and (
                slide == Move.TOP or slide == Move.LEFT)
        # check if the move is acceptable
        acceptable: bool = acceptable_top or acceptable_bottom or acceptable_left or acceptable_right
        # if it is
        if acceptable:
            # take the piece
            piece = self._board[from_pos]
            # if the player wants to slide it to the left
            if slide == Move.LEFT:
                # for each column starting from the column of the piece and moving to the left
                for i in range(from_pos[1], 0, -1):
                    # copy the value contained in the same row and the previous column
                    self._board[(from_pos[0], i)] = self._board[(
                        from_pos[0], i - 1)]
                # move the piece to the left
                self._board[(from_pos[0], 0)] = piece
            # if the player wants to slide it to the right
            elif slide == Move.RIGHT:
                # for each column starting from the column of the piece and moving to the right
                for i in range(from_pos[1], self._board.shape[1] - 1, 1):
                    # copy the value contained in the same row and the following column
                    self._board[(from_pos[0], i)] = self._board[(
                        from_pos[0], i + 1)]
                # move the piece to the right
                self._board[(from_pos[0], self._board.shape[1] - 1)] = piece
            # if the player wants to slide it upward
            elif slide == Move.TOP:
                # for each row starting from the row of the piece and going upward
                for i in range(from_pos[0], 0, -1):
                    # copy the value contained in the same column and the previous row
                    self._board[(i, from_pos[1])] = self._board[(
                        i - 1, from_pos[1])]
                # move the piece up
                self._board[(0, from_pos[1])] = piece
            # if the player wants to slide it downward
            elif slide == Move.BOTTOM:
                # for each row starting from the row of the piece and going downward
                for i in range(from_pos[0], self._board.shape[0] - 1, 1):
                    # copy the value contained in the same column and the following row
                    self._board[(i, from_pos[1])] = self._board[(
                        i + 1, from_pos[1])]
                # move the piece down
                self._board[(self._board.shape[0] - 1, from_pos[1])] = piece
        return acceptable



### We use this structure to encode the Board
class State(Node):


    def __init__(self,board, row=None, col=None, direction=None) -> None:
        super().__init__()
        self.board = board
        self.moves = dict()
        self.current_player = "X"
        self.row = row
        self.col = col
        self.direction = direction
        self.hash_key = self.generate_hash_key(self.board)

    
    def set_board(self, board) -> None:
        self.board = board

    def add_move(self, board) -> None:
        self.moves[board] = 3

    ## 
    def print_board_from_state(self):
        # Extract 'X' and 'O' locations from the state
        x_location = self.board & 0xFFFFFFFF  # Bits 0 to 31
        o_location = (self.board >> 32) & 0xFFFFFFFF  # Bits 32 to 63

        # Initialize an empty 5x5 board
        board = [[' ' for _ in range(5)] for _ in range(5)]

        # Update the board with 'X' and 'O' positions
        for i in range(25):
            row = i // 5
            col = i % 5
            if (x_location >> i) & 1:
                board[row][col] = "⭕"  ### O
            elif (o_location >> i) & 1:
                board[row][col] = "❌"  ### X
            else:
                board[row][col] = "🔳"
        print('-' * 23)
        # Print the board with grboard
        for row in reversed(board):
            print(' | '.join(reversed(row)))
            print('-' * 23)
        print()
    

    ## returns the board with players swapped
    def swap_players(self, board):
        right_prova = board >> 32
        left_prova = board << 32
        bitmask = (1 << 64) - 1
        left_prova = left_prova & bitmask
        switched = right_prova | left_prova        
        return switched      

    ## shift and symmetries/rotations 
    def shift_right(self, player, row, col, board):
        if player != "X" and player != "O":
            raise(TypeError("Invalboard player board"))
        C = 0
        B = 0
        c_index = 24 - (row + 4*row)
        C = 1 << c_index
        for i in range(c_index, c_index-(col+1),-1):
            B |= 1 << i
        for i in range(c_index+32, c_index+32-(col+1), -1):
            B |= 1 << i
        shifted_board = (((board & B) >> 1) & B) | (board & ~B) | C
        return shifted_board
    
    def shift_left(self, player, row,col, board):
        if player != "X" and player != "O":
            raise(TypeError("Invalboard player board"))     
        C = 0
        B = 0
        c_index = 24 - ((row +4) + 4*row)
        C = 1 << c_index
        for i in range(c_index, c_index+(5-col)):
            B |= 1 << i
        for i in range(c_index+32, c_index+32+(5-col)):
            B |= 1 << i
        shifted_board = ((((board & B) << 1) & B) | (board & ~B) | C)
        return shifted_board

    def shift_up(self, player, row, col, board):
        if player != "X" and player != "O":
            raise(TypeError("Invalboard player board"))        
        C = 0
        B = 0
        c_index = 24 - (col + 20)
        C = 1 << c_index
        for i in range(c_index, c_index + (5-row) * 5, 5):
            B |= 1 << i
        for i in range(c_index + 32, c_index + 32 + (5-row) * 5, 5):
            B |= 1 << i
        shifted_board =(((board & B) << 5) & B) | (board & ~B) | C
        return shifted_board

    def shift_down(self, player, row, col, board):
        if player != "X" and player != "O":
            raise(TypeError("Invalboard player board"))
        C = 0
        B = 0
        c_index = 24 - col
        C = 1 << c_index
        for i in range(c_index, c_index - (row * 5)-1, -5):
            B |= 1 << i
        for i in range(c_index + 32, (c_index + 32) - (row * 5)-1, -5):
            B |= 1 << i
        shifted_board =(((board & B) >> 5) & B) | (board & ~B) | C
        return shifted_board
    
    def rotate_clockwise(self, board):
         shifted_board = self.d2_symmetry(board)
         shifted_board = self.horizontal_symmetry(shifted_board)
         return shifted_board       
    
    def rotate_counterclockwise(self,board):
         shifted_board = self.d2_symmetry(board)
         shifted_board = self.vertical_symmetry(shifted_board)
         return shifted_board   
    
    def vertical_symmetry(self, board):
        old_o = board & int("1111111111111111111111111", 2)
        old_x = (board >> 32) & int("1111111111111111111111111", 2)
        new_o = 0
        new_x = 0
        for b in range(25):
            col = b//5
            old_bit = (old_o >> b) & 1
            new_index = abs(4-(b-5*col)) + 5*col
            new_bit = old_bit << new_index
            new_o |= new_bit
        for b in range(25):
            col = b//5
            old_bit = (old_x >> b) & 1
            new_index = abs(4-(b-5*col)) + 5*col
            new_bit = old_bit << new_index
            new_x |= new_bit
        new_x = new_x << 32
        return new_x | new_o

    def horizontal_symmetry(self,board):
        old_o = board & int("1111111111111111111111111", 2)
        old_x = (board >> 32) & int("1111111111111111111111111", 2)
        new_o = 0
        new_x = 0
        for b in range(25):
            col = b//5
            row = b % 5
            old_bit = (old_o >> b) & 1
            new_index = abs(20-(5*col))+row
            new_bit = old_bit << new_index
            new_o |= new_bit
        for b in range(25):
            col = b//5
            row = b % 5
            old_bit = (old_x >> b) & 1
            new_index = abs(20-(5*col))+row
            new_bit = old_bit << new_index
            new_x |= new_bit
        new_x = new_x << 32
        return new_x | new_o
    
    def d1_symmetry(self, board):
        old_o = board & int("1111111111111111111111111", 2)
        old_x = (board >> 32) & int("1111111111111111111111111", 2)
        new_o = 0
        new_x = 0
        for b in range(25):
            col = b//5
            row = b % 5
            old_bit = (old_o >> b) & 1
            new_index = 5*row + col
            new_bit = old_bit << new_index
            new_o |= new_bit
        for b in range(25):
            col = b//5
            row = b % 5
            old_bit = (old_x >> b) & 1
            new_index = 5*row + col
            new_bit = old_bit << new_index
            new_x |= new_bit
        new_x = new_x << 32
        return new_x | new_o

    def d2_symmetry(self, board):
        old_o = board & int("1111111111111111111111111", 2)
        old_x = (board >> 32) & int("1111111111111111111111111", 2)
        new_o = 0
        new_x = 0
        for b in range(25):
            col = b//5
            row = b % 5
            old_bit = (old_o >> b) & 1
            new_index = (20 - 5*row) + 4 - col
            new_bit = old_bit << new_index
            new_o |= new_bit
        for b in range(25):
            col = b//5
            row = b % 5
            old_bit = (old_x >> b) & 1
            new_index = (20 - 5*row) + 4 - col
            new_bit = old_bit << new_index
            new_x |= new_bit
        new_x = new_x << 32
        return new_x | new_o
    

    def generate_symmetries(self, board):
        '''Returns a list of all possible symmetries + rotations of the given board'''
        sym = [State(board), State(self.vertical_symmetry(board)), State(self.horizontal_symmetry(board)),
                     State(self.d1_symmetry(board)), State(self.d2_symmetry(board)), State(self.rotate_clockwise(board)),
                        State(self.rotate_counterclockwise(board))]
        return sym

    def check_symmetries(self, boards_dict, board) -> int:
        '''Checks if a given board its already present in a pre-existent list of positions, 
            consboardering its original form and all its possible symmetries'''
        
        sym = [State(board), State(self.vertical_symmetry(board)), State(self.horizontal_symmetry(board)),
                     State(self.d1_symmetry(board)), State(self.d2_symmetry(board)), State(self.rotate_clockwise(board)),
                        State(self.rotate_counterclockwise(board))]
        i = 0
        for s in sym:
            i+=1
            if s.board in boards_dict:
                return 0
        return 1

    def generate_moves(self, pos, player) -> list:
        moves = list()

        frontiers = [UPPER_FRONTIER, LOWER_FRONTIER, LEFT_FRONTIER, RIGHT_FRONTIER]

        for frontier in frontiers:
            for i in frontier:
                occupied = (pos >> 32) << i
                occupied &= 16777216

                if occupied != 16777216:
                    directions = ["up", "down", "left", "right"]

                    if i in UPPER_FRONTIER:
                        directions.remove("down")
                    elif i in LOWER_FRONTIER:
                        directions.remove("up")
                    if i in LEFT_FRONTIER:
                        directions.remove("right")
                    elif i in RIGHT_FRONTIER:
                        directions.remove("left")

                    for direction in directions:
                        add = getattr(self, f"shift_{direction}")("O", i // 5, i % 5, pos)
                        moves_boards = []
                        for m in moves:
                            if player=="X":
                                moves_boards.append(self.swap_players(m.board))
                            else:
                                moves_boards.append(m.board)
                        if self.check_symmetries(moves_boards, add) != 0 and add!=pos:
                            ### ADDING MOVE
                            new_state = State(self.swap_players(add) if player == "X" else add, 
                                            row = i//5, col=i%5, direction=direction)
                            moves.append(new_state)
        return moves

    ### wrapper for generate_moves
    def create_position(self, player, in_game=False) -> list:
        '''
        Generates all possible moves for player O, given a certain board
        '''
        if player == "X":               ###always works on Os
            board = self.swap_players(self.board)       
        moves = self.generate_moves(board if player == "X" else self.board, player)
        if player == "X":               ###always works on Os
            board = self.swap_players(self.board)  
        return moves



    #### CHECK WINNER
    def check_winner(self):
        o_draw = self.board & 33554431
        x_draw = (self.board >> 32) & 33554431
        if o_draw | x_draw == 33554431:
            return "D" #stands for draw
        for o_comb in WINNING_COMBS:
            x_comb = o_comb << 32
            o_and = self.board & o_comb
            x_and = self.board & x_comb
            if o_and == o_comb:
                return "O"
            elif x_and == x_comb:
                return "X"
        return "-"
    

    ### aggiustato
    def find_children(self, player):
        "All possible successors of this board state"
        if self.check_winner()!="-":
            print("board is terminal!")
            return None    
        return self.create_position(player)


     
    def find_random_child(self, player=None):
        '''Returns a random move'''
        return choice(self.create_position(player)) 

    
    def find_the_child(self, monteQ, player=None, reverse=False):
        '''Returns the best move'''
        if reverse:
            return min(self.create_position(player), key=lambda y: monteQ[y] if y in monteQ.keys() else float("inf"))
        return max(self.create_position(player), key=lambda y: monteQ[y] if y in monteQ.keys() else float("-inf"))


    def is_terminal(self):
        "Returns True if the node has no children" 
        return self.check_winner()!="-"

    
    def reward(self):
        if not self.is_terminal():
            return
        win = self.check_winner()
        if win =="O":  ### I won
            add = 3
        elif win =="D":
            add = 1
        else:
            add = -1
        
        return add

    ### utility to actually hash at symmetry/rotation level
    def generate_hash_key(self, board):
        sym = [self.board, self.vertical_symmetry(board), self.horizontal_symmetry(board),
                     self.d1_symmetry(board), self.d2_symmetry(board), self.rotate_clockwise(board),
                        self.rotate_counterclockwise(board)]
        symset = set(sym)
        return sum(list(symset))
    
    ### made it resistant to symmetry/rotation
    def __hash__(self):
        "Nodes must be hashable"
        return hash(self.hash_key)

    ### resistant to symmetry/rotation
    def __eq__(self,node2):
        "Nodes must be comparable" 
        board_with_sym = self.generate_symmetries(self.board)   
        for b in board_with_sym:
            if b.board == node2.board:
                return True            
        return False