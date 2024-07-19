import random
from game import Game, Move, Player, State
from MCTS import MCTS
from tqdm import tqdm
from collections import defaultdict
import pickle


class RandomPlayer(Player):
    def __init__(self) -> None:
        super().__init__()

    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        from_pos = (random.randint(0, 4), random.randint(0, 4))
        move = random.choice([Move.TOP, Move.BOTTOM, Move.LEFT, Move.RIGHT])
        return from_pos, move

class OffMonteCarloPlayer(Player):
    def __init__(self, train_with_checkpoints=True, load_model=False, log_folder = None) -> None:
        super().__init__()
        self.checkpoint = train_with_checkpoints
        self.log_folder = log_folder
        self.my_symbol = "-"
        
        if load_model:
          q,n = self.load_model(log_folder)
          self.tree = MCTS(q=q, n=n)
          print(f"succesfully loaded Q (len {len(self.tree.Q)}) and N (len {len(self.tree.N)})")            
        else:
            self.tree = MCTS()



    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        
        def fromNumPy(np_board):
          rows, cols = np_board.shape
          ret = 0
          for i in range(rows):
              for j in range(cols):
                  if np_board[i,j]==0:
                    ret |= 1 << (24 - 5*i - j) 
                  elif np_board[i,j]==1:
                    ret |= 1 << (32 + (24 - 5*i - j)) 
          return ret      
        
        self.my_symbol = "O" if game.current_player_idx==0 else "X"
        opponent = "O" if self.my_symbol=="X" else "X"
        print(f"MC plays {self.my_symbol}")

        ### some manipulation between our data structures and the given ones
        binary_current_board = fromNumPy(game._board)
        ret_board = self.tree.choose(State(binary_current_board), opponent=opponent) 

        from_pos = (ret_board.col, ret_board.row)
        if ret_board.direction=="up":
            move = Move.BOTTOM
        elif ret_board.direction=="down":
            move = Move.TOP
        elif ret_board.direction=="left":
            move = Move.RIGHT
        elif ret_board.direction=="right":
            move = Move.LEFT            
        return from_pos, move
        
    def train(self):
        epochs = range(100000)
        self.age = epochs
        save =0
        n_check = 0
        print("Starting training procedure....")
        for item in tqdm(epochs, desc="Training...", unit="item"):
            self.tree.do_rollout(State(0))
            save+=1
            if self.checkpoint and save%1000==0:
                self.save_model(self.log_folder+f"/q_{n_check}", self.log_folder+f"/n_{n_check}")
                n_check+=1
        self.save_model(self.log_folder+f"/last_q", self.log_folder+f"/last_n")
        self.save_age()

    def save_model(self, path_q, path_n):
        try:
          with open(path_q, 'wb') as file:
            pickle.dump(self.tree.Q, file)
          with open(path_n, 'wb') as file:
            pickle.dump(self.tree.N, file)
          
          print(f"Successfully saved Q and N to {path_q} and {path_n}")
        except Exception as e:
            print(f"Error: {e}")

    
    def save_age(self):
        with open('MCplayer ages', 'wb') as file:
            pickle.dump(self.age, file)

    def load_model(self, path):
        try:
            with open(path+"/q_0", 'rb') as file:
                q = pickle.load(file) 
            with open(path+"/n_0", 'rb') as file:
                n = pickle.load(file) 
            return q, n
        except FileNotFoundError:
            print("Q or N file not found. Loading empty dictionaries....")
            return defaultdict(float),defaultdict(int)
        except Exception as e:
            print(f"Error: {e}")
            raise


class OnMonteCarloPlayer(Player):
    def __init__(self,step=50) -> None:
        super().__init__()
        self.step = step
        self.my_symbol = "-"
        self.tree = MCTS()

    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        
        def fromNumPy(np_board):
          rows, cols = np_board.shape
          ret = 0
          for i in range(rows):
              for j in range(cols):
                  if np_board[i,j]==0:
                    ret |= 1 << (24 - 5*i - j) 
                  elif np_board[i,j]==1:
                    ret |= 1 << (32 + (24 - 5*i - j)) 
          return ret      
                 
        self.my_symbol = "O" if game.current_player_idx==0 else "X"
        opponent = "O" if self.my_symbol=="X" else "X"
        print(f"MC plays {self.my_symbol}")


        binary_current_board = fromNumPy(game._board)
        
        epochs = range(self.step)
        for item in tqdm(epochs, desc="Rolling...", unit="item"):
          self.tree.do_rollout(State(binary_current_board))
        ret_board = self.tree.choose(State(binary_current_board), opponent=opponent) 

        from_pos = (ret_board.col, ret_board.row)
        if ret_board.direction=="up":
            move = Move.BOTTOM
        elif ret_board.direction=="down":
            move = Move.TOP
        elif ret_board.direction=="left":
            move = Move.RIGHT
        elif ret_board.direction=="right":
            move = Move.LEFT            
        return from_pos, move

class MixedMonteCarloPlayer(Player):
    def __init__(self, train_with_checkpoints=True, load_model=False, log_folder = None, step=100) -> None:
        super().__init__()
        self.checkpoint = train_with_checkpoints
        self.log_folder = log_folder
        self.my_symbol = "-"
        self.step = step
        
        if load_model:
          q,n = self.load_model(log_folder)
          self.tree = MCTS(q=q, n=n)
          print(f"succesfully loaded Q (len {len(self.tree.Q)}) and N (len {len(self.tree.N)})")            
        else:
            self.tree = MCTS()



    def make_move(self, game: 'Game') -> tuple[tuple[int, int], Move]:
        
        def fromNumPy(np_board):
          rows, cols = np_board.shape
          ret = 0
          for i in range(rows):
              for j in range(cols):
                  if np_board[i,j]==0:
                    ret |= 1 << (24 - 5*i - j) 
                  elif np_board[i,j]==1:
                    ret |= 1 << (32 + (24 - 5*i - j)) 
          return ret      
        
        self.my_symbol = "O" if game.current_player_idx==0 else "X"
        opponent = "O" if self.my_symbol=="X" else "X"
        print(f"MC plays {self.my_symbol}")


        binary_current_board = fromNumPy(game._board)
        for _ in range(self.step):
          self.tree.do_rollout(State(binary_current_board))
        ret_board = self.tree.choose(State(binary_current_board), opponent=opponent) 
        from_pos = (ret_board.col, ret_board.row)
        if ret_board.direction=="up":
            move = Move.BOTTOM
        elif ret_board.direction=="down":
            move = Move.TOP
        elif ret_board.direction=="left":
            move = Move.RIGHT
        elif ret_board.direction=="right":
            move = Move.LEFT            
        return from_pos, move
        
    def train(self):
        epochs = range(100000)
        self.age = epochs
        save =0
        n_check = 0
        print("Starting training procedure....")
        for item in tqdm(epochs, desc="Training...", unit="item"):
            self.tree.do_rollout(State(0))
            save+=1
            if self.checkpoint and save%1000==0:
                self.save_model(self.log_folder+f"/q_{n_check}", self.log_folder+f"/n_{n_check}")
                n_check+=1
        self.save_model(self.log_folder+f"/last_q", self.log_folder+f"/last_n")
        self.save_age()

    def save_model(self, path_q, path_n):
        try:
          with open(path_q, 'wb') as file:
            pickle.dump(self.tree.Q, file)
          with open(path_n, 'wb') as file:
            pickle.dump(self.tree.N, file)
          
          print(f"Successfully saved Q and N to {path_q} and {path_n}")
        except Exception as e:
            print(f"Error: {e}")

    
    def save_age(self):
        with open('MCplayer ages', 'wb') as file:
            pickle.dump(self.age, file)

    def load_model(self, path):
        try:
            with open(path+"/q_0", 'rb') as file:
                q = pickle.load(file) 
            with open(path+"/n_0", 'rb') as file:
                n = pickle.load(file) 
            return q, n
        except FileNotFoundError:
            print("Q or N file not found. Loading empty dictionaries....")
            return defaultdict(float),defaultdict(int)
        except Exception as e:
            print(f"Error: {e}")
            raise

if __name__ == '__main__':
    g = Game()

    ### GAME ###
    random_player = RandomPlayer()
    mc_player = OffMonteCarloPlayer(load_model=True, log_folder=r"your/log/path")
    mixed_player =  MixedMonteCarloPlayer(load_model=True, log_folder=r"your/log/path")
    #winner = g.play(mixed_player, random_player)
    #print(f"Winner : Player {winner}")

    ### TRAINING ###
    #mc_player.train()
