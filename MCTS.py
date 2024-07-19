"""
A minimal implementation of Monte Carlo tree search (MCTS) in Python 3
Luke Harold Miles, July 2019, Public Domain Dedication
See also https://en.wikipedia.org/wiki/Monte_Carlo_tree_search
https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1
"""
from abc import ABC, abstractmethod
from collections import defaultdict
import math
from random import random, choice
import numpy


class Node(ABC):
    """
    A representation of a single board state.
    MCTS works by constructing a tree of these Nodes.
    Could be e.g. a chess or checkers board state.
    """

    @abstractmethod
    def find_children(self):
        "All possible successors of this board state"
        return list()

    @abstractmethod
    def find_random_child(self):
        "Random successor of this board state (for more efficient simulation)"
        return None

    @abstractmethod
    def find_the_child(self):
        "Random successor of this board state (for more efficient simulation)"
        return None

    @abstractmethod
    def is_terminal(self):
        "Returns True if the node has no children"
        return True

    @abstractmethod
    def reward(self):
        "Assumes `self` is terminal node. 1=win, 0=loss, .5=tie, etc"
        return 0

    @abstractmethod
    def __hash__(self):
        "Nodes must be hashable"
        return 123456789

    @abstractmethod
    def __eq__(node1, node2):
        "Nodes must be comparable"
        return True
    



class MCTS:
    "Monte Carlo tree searcher. First rollout the tree then choose a move."

    def __init__(self, player="O", checkpoint=None, exploration_weight=numpy.sqrt(2), epsilon = 0.4, opponent_level=0.1 ,q = defaultdict(float), n = defaultdict(int)):
        self.Q = q  # total reward of each node
        self.N = n  # total visit count for each node
        self.children = dict()  # children of each (visited?) node
        self.exploration_weight = exploration_weight
        self.epsilon = epsilon
        self.player = player
        self.checkpoint = checkpoint
        self.opponent_level = opponent_level

    def change_player(self):
        if self.player == "X":
            return "O"
        elif self.player=="O":
            return "X"

    def choose(self, node : Node, opponent="X"):
        "Choose the best successor of node. (Choose a move in the game)"
        if node.is_terminal():
            raise RuntimeError(f"choose called on terminal node {node}")

        if opponent=="O":
            myself = "X"
        else:
            myself="O"

        ## i didn't see this node in training, lets return a random move
        if node not in self.Q:
            return node.find_random_child(myself)


        def score(n, reverse=False):
            if self.N[n] == 0:
                return float("-inf") if reverse==False else float("inf")  # avoid unseen moves
            return self.Q[n] / self.N[n]  # average reward

        ## if node already visited, return the best childS

        if opponent!=self.player:
            ret =  max(node.find_children(myself), key=score)
            print(f"chose node {ret.board} with score {score(ret)}")
            return ret
        else:
            ret = min(node.find_children(myself), key=lambda n: score(n, reverse=True))      
            print(f"chose node {ret.board} with score {score(ret, reverse=True)}")
            return ret


    def do_rollout(self,node):
        "Make the tree one layer better. (Train for one iteration.)"
        path = self._select(node)
        leaf = path[-1]

        if len(path)%2==0:
            turn = self.change_player()
        else:
            turn = self.player

        self._expand(leaf, turn)  ### adds children to leaf
        reward = self._simulate(leaf, turn)
        self._backpropagate(path, reward)


    def _select(self, node : Node):
        "Find an unexplored descendent of `node`"
        rank = 0
        path = []
        while True:
            path.append(node)
            if node not in self.children or not self.children[node]:
                # node is either unexplored or terminal
                return path
            
            ### node is explored and not terminal, i.e. it has children
            unexplored = self.children[node] - self.children.keys()
            ### pop one, append to path and return 
            if unexplored:
                n = unexplored.pop()
                path.append(n)
                return path
            
            ### node is not terminal, all children have been explored, just descend one layer
            node = self._uct_select(node, rank)  # descend a layer deeper

            ### if node is already in path ==> we're in a loop. That's fine, just force uct to choose another way to not get stuck
            if node not in path:
                rank = 0
            else:
                rank+=1


    def _expand(self, node : Node, player):
        "Update the `children` dict with the children of `node`"
        if node in self.children:
            return  # already expanded
        self.children[node] = node.find_children(player)

    def _simulate(self, node : Node, last_move):
        "Returns the reward for a random simulation (to completion) of `node`"
        turn = last_move
        while True:
            if node.is_terminal():
                reward = node.reward()
                return reward

            if random() < self.epsilon:
                node = node.find_random_child(turn)

            else:
                if random() < self.opponent_level:
                    node = node.find_the_child(self.Q, player= turn, reverse=True)
                else:
                    node = node.find_the_child(self.Q, player= turn)
           
            if turn == "O":
                turn = "X"
            else:
                turn = "O"


    def _backpropagate(self, path, reward):
        "Send the reward back up to the ancestors of the leaf"     
        for node in reversed(path):
                self.N[node] += 1
                self.Q[node] += reward          

    def _uct_select(self, node, rank):
        "Select a child of node, balancing exploration & exploitation"

        # All children of node should already be expanded:
        assert all(n in self.children for n in self.children[node])

        log_N_vertex = math.log(self.N[node])

        def uct(n):
            "Upper confidence bound for trees"
            return self.Q[n] / self.N[n] + self.exploration_weight * math.sqrt(
                log_N_vertex / self.N[n]
            )
        sorted_uct = sorted(self.children[node], key=uct, reverse=True)
        return sorted_uct[rank]


