# Exam Project - Winning *Quixo* with Reinforcement Learning
This repo contains the final draft of the CI exam, a.y. 2023/24.
We developed a Monte Carlo Tree Search based algorithm to train an agent in order to win the Quixo game.
## Authors
The contributors of this repo are:
* [Stefano Barcio](https://github.com/stefbarcio/computational_intelligence_23-24), s320174 
* [Luca Faieta](https://github.com/LucaFaieta/Computational_Intelligence), s323770

## Reproduce our code
You're welcome to verify our conclusions using the code in this folder. The game is managed in the `main` function. It's enough to declare an instance of any of the player classes and start the `game.play()` function.

***ATTENTION!***: if you're using the offline or mixed agent, remember to change the `log_folder` parameter when declaring the player, in order to match the actual path of the logs folder on your machine

## QUIXO
QUIXO [3] is a game inspired by the popular Tic Tac Toe game.  It is played on a 5x5 board, and each player has a set of cubes with X or O markings on their faces. The objective of the game is to be the first to form an unbroken line of your own symbol (X or O) horizontally, vertically, or diagonally on the board.
What makes it different from its most popular counterpart it's the possibility for a player to move the opponent's tiles, in order to push him away from victory, while simoultaneously trying to form a winning combination for his own.

## Solution Overview
We decided to develop our personal version of Monte Carlo Tree Sampling. 

MCTS is a well known reinforcement learning algorithm, and is particularly well suited to solve strategy-based games like QUIXO. The main reason that led to our choice is the remarkable capability of MCTS to be indipendent from any rule or strategy in the game. Since we were not familiar with QUIXO, the idea of implementing a non-trivial heuristic for the game sounded prohibitive, and so we tried to find a way to circumvent this difficulty, and Monte Carlo provided us just the right solution.

We utilized code from a public repository [2] to implement the skeleton of MCTS. The content of how main implementations follows:

### State space distribution

 MCTS, as the name says, was originally created to work on a state-space modeled like a tree. The very peculiarity of QUIXO, i.e. the possibility of taking a move that adds nothing new to the board and just shuffles its element, makes possible to come back to previously visited states quite easily. In fact, our tests showed that this is a quite common occurrence, and makes the base version of MCTS completely useless.

This property makes the state space of the game a cyclic graph, so we needed to adapt the existing code to work with this constraint

 The way we solved this is quite simple: we retain the tree structure of the code, but consider the case when a loop in the nodes occurs. 
 
 The idea is that a loop in the game trajectory is not necessarily a bad thing: one could note that, since the game ends in a draw when all tiles are occupied, in the late game the goal of a smart agent would not be to continue adding things, but rather trying to move the already taken tiles to form a winning combination. It's obvious how this behaviour can easily generate loops in a game trajectory.

 On the other hand, an agent that moves the board in a way that doesn't change it at all (i.e. passes its turn to the opponent) it's something that we didn't want our agent to do. To solve this we banned the possibility of generating the same board twice in a row. It's still possible that this kind of move could actually be the best one for some weird game trajectory, but it seemed unreasonable to explore this kind of situation.

 When a loop actually happens, and the agent finds itself in a node that he visited soon before, we just tell it to continue its exploration down the tree, taking care of not choosing once again the same child that led to that particular loop. This does not mathematically guarantee that the algorithm won't loop forever, but it gave us a reasonable confidence that the exploration would go on without stalling, and even exploring new paths in the tree.

 ### Boards Symmetry
 Quixo, like other tiles based games like Tic Tac Toe, implicitly carries a great degree of symmetry in its possible number of states. From the agent point of view, every board its perfectly equivalent to all its possible symmetries and rotations, since the search for the best move would lead to the same result in all cases.

 By modifying the `__eq__` and `__hash__`  methods of our State class we decided to create an higher level class of equivalence, so that the algorithm actually sees a board as the same object as every one of its possible rotations and symmetries.

 This stratregy leads to two significative results. On one hand it allows us to reduce the state space by a factor of 6 (horizontal, vertical, diagonal1, diagonal2 symmetries, clockwise and counterclockwise rotations) while on the other one it makes the algorithm aggregate the learned features in a much more powerful way, thus leading to a faster learning rate

 ### Binary State Representation
 Since we needed to consider a very high number of states and iterate on them the highest possible number of times, efficiency was a key concern in our minds.


 We found a very interesting way to encode the game board [1]. It consists of just one  64-bit integer to codify a whole board. The first 24 bits map the "O" positions, while the bits from 32 to 56 map the "X" positions, with 0s padding between those two sections.

 This implementation allowed us to manage every single manipulation of the board with minimal machine effort. It was hard to deduce the right set of operations for all of them, but what we have in the end is a system that performs every possible shift and every possible symmetry/rotation of the board just with (one or two) bitwise operations.

 This approach would surely benefit from a lower-level implementation rather than Python, but since the learning stage of our algorithm is completely detached from the actual play (both in terms of data structures and procedures) an interesting possibility for further implementation would be to actually re-write the learning part of the program in C/C++ or some other low-level languages to actually benefit from the nature of the encoding.

 However, at least in terms of space, we are quite confident that this is the best possible encoding of the board, regardless of the nature of the implementation.

## Our Agents

### Random Player
We didn't touch it at all, and it serves only for test purposes.

### Online MonteCarlo Player
We have three versions of the MCTS implementation. They all share the same structure for learning game trajectory: what changes its the way they manage the game.

The online versions receives the state of the game from the opponent, and then performs a small number of rollouts from that board to try and find the best move to take. 

This naturally decreases its overall knowledge of the game, but makes it a (rather) fast implementation that still manages to beat RandomPlayer frequently

### Offline MonteCarlo Player

This istance of MonteCarlo is thought to work in two stages: first, it performs a very high number of rollouts, all starting from the root of the game, and then stores them in a dictionary in the form `{any_board: best_move}`and stores it in the file system. Then, when the game starts, it receives the board from the opponent, looks up for it in the dictionary and returns the best move that it learned.

This solution requires at least one long training session, but it gives a better knowledge of the State space compared to the online version.

Still, without a *really* long phase of training, it isn't able to reach the leafs of the tree often enough to be reliable, especially in the late stages of the game

### Mixed MonteCarlo Player
This model combines the pros of Online and Offline approaches, making it the best solution we found until now.

It still loads a pre-learned dictionary of moves, but when it encounters an unseen state, rather than playing randomly it performs a small number of rollouts (like the online version) to gain at least some knowledge of the path its opponent is choosing.

With this approach we can leverage the high knowledge of the shallow layers of the tree, brought by the Offline Player, while retaining the ability of *never* playing a blind move at any stage of the game, that is the strong point of the Online version




## Possible Extensions
This project was done in the context of an academic test, and it's far from perfect. Some suggestions that we leave for future implementations (ours or by someone else interested) are:

  1. **Exploiting the Binary representation** as we said before, our kind of representation could highly benefit from a lower-level implementation rather than Python, to increase performance of the learning stage, especially for the offline agent

  2. **Better tuning of the MCTS** in the time at our disposal, we didn't really find the correct combination of hyperparameters to balance exploration and exploitation. Further experiments could be run to find the optimal set of parameters, possibly including discount factors or other RL typical strategies

  3. **Exploring possible game heuristics** while this didn't seem the right approach to us, it could be reasonable to introduce some heuristic to the game, particularly in the late game (e.g. acknowledging if a certain move makes the opponent win in N moves, or assigning some sort of intermediate score to non-terminal boards)


## References 

[[1]](https://arxiv.org/abs/2007.15895). "Quixo is Solved", Satoshi Tanaka et Al.

[[2]](https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1). , MonteCarlo Tree Search repository, by qpwo

[[3]](https://www.pergioco.net/5/quixo.html). QUIXO rules