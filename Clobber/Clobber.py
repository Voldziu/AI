import numpy as np
import time
import copy

from MinimaxAgent import *



class ClobberGame:
    def __init__(self,board=None,size=(5,6)):

        self.size = size

        if board is None:

            self.board = np.empty(size, dtype=str)
            for i in range(size[0]):
                for j in range(size[1]):
                    if (i + j) % 2 == 0:
                        self.board[i, j] = 'W'
                    else:
                        self.board[i, j] = 'B'
        else:
            self.board = board

    def print_board(self):

        for i in range(self.size[0]):
            row = ' '.join(self.board[i])
            print(row)

    def is_game_over(self):


        return (len(self.get_possible_moves('B')) == 0 and
                len(self.get_possible_moves('W')) == 0)

    def get_possible_moves(self, player):

        moves = []

        # Kierunki ruchu (góra, dół, lewo, prawo)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for i in range(self.size[0]):
            for j in range(self.size[1]):

                if self.board[i, j] == player: # W or B

                    for di, dj in directions:
                        ni, nj = i + di, j + dj


                        if 0 <= ni < self.size[0] and 0 <= nj < self.size[1]: #if within bounds

                            opponent = 'W' if player == 'B' else 'B'
                            if self.board[ni, nj] == opponent:
                                moves.append((i, j, ni, nj))

        return moves

    def make_move(self, move):

        # copy
        new_board = copy.deepcopy(self.board)

        # make move
        x1, y1, x2, y2 = move
        piece = new_board[x1, y1]
        new_board[x2, y2] = piece  # set piece
        new_board[x1, y1] = '_'  # delete piece

        return ClobberGame(new_board, self.size)

    def evaluate(self, player, heuristic):

        return heuristic.evaluate(self, player)


def play_game(agent1, agent2, initial_board=None, size=(5, 6), max_rounds=100, silent=False):
    """
    Play a complete game between two agents.

    Args:
        agent1: Agent for player 1 (black).
        agent2: Agent for player 2 (white).
        initial_board: Optional starting board.
        size: Board size.
        max_rounds: Maximum number of rounds, to prevent infinite games.
        silent: Whether to suppress output to console.

    Returns:
        tuple: (final_game, result_dict) where result_dict contains statistics
    """
    game = ClobberGame(initial_board, size)
    current_player = 'B'  # Black first
    rounds = 0

    # Stats tracking
    total_nodes_black = 0
    total_nodes_white = 0
    total_time_black = 0
    total_time_white = 0

    if not silent:
        print("Start Board:")
        game.print_board()
        print()

    while not game.is_game_over() and rounds < max_rounds:
        if current_player == 'B':
            rounds += 1
            if not silent:
                print(f"Round {rounds}:")

        if not silent:
            print(f"Player's move: {current_player}")

        # Choose move
        if current_player == 'B':
            start_time = time.time()
            move = agent1.get_move(game)
            end_time = time.time()

            nodes = agent1.nodes_visited
            elapsed = end_time - start_time

            # Update stats
            total_nodes_black += nodes
            total_time_black += elapsed

            if not silent:
                print(f"Nodes visited: {nodes}")
                print(f"Execution time: {elapsed:.4f} s")

            # Register move for adaptive agent
            if isinstance(agent2, AdaptiveMinimaxAgent):
                agent2.register_opponent_move(move)

        else:  # current_player == 'W'
            start_time = time.time()
            move = agent2.get_move(game)
            end_time = time.time()

            nodes = agent2.nodes_visited
            elapsed = end_time - start_time

            # Update stats
            total_nodes_white += nodes
            total_time_white += elapsed

            if not silent:
                print(f"Nodes visited: {nodes}")
                print(f"Execution time: {elapsed:.4f} s")

            # Register move for adaptive agent
            if isinstance(agent1, AdaptiveMinimaxAgent):
                agent1.register_opponent_move(move)

        if not silent:
            print(f"Selected move: {move}")

        # Make the move
        game = game.make_move(move)

        if not silent:
            print("Board after move:")
            game.print_board()
            print()

        # Switch player
        current_player = 'W' if current_player == 'B' else 'B'

    # Determine winner
    winner = 'W' if current_player == 'B' else 'B'  # Player who made the last move

    # Create result dictionary
    result = {
        "winner": winner,
        "rounds": rounds,
        "nodes_black": total_nodes_black,
        "nodes_white": total_nodes_white,
        "time_black": total_time_black,
        "time_white": total_time_white
    }

    return game, result


def handle_players_agent_choice(player):
    print(f"\nParameters for the player ({player}):")
    print("Enter maximum search depth:")
    depth = int(input() or "3")

    print("Choose heuristic (0-5):")
    print("0: Mobility difference")
    print("1: Number of mobile pieces")
    print("2: Center control")
    print("3: Number of adjacent opponent pieces")
    print("4: Opponent blocking")
    print("5: Adaptive (changes strategy based on game phase)")
    heuristic_choice = int(input() or "0")

    print("Use alpha-beta pruning? (y/n)")
    use_alpha_beta = input().lower() != 'n'
    agent = None
    if heuristic_choice == 0:
        heuristic = MobilityDifferenceHeuristic()
    elif heuristic_choice == 1:
        heuristic = PieceMobilityHeuristic()
    elif heuristic_choice == 2:
        heuristic = CenterControlHeuristic()
    elif heuristic_choice == 3:
        heuristic = AdjacentOpponentHeuristic()
    elif heuristic_choice == 4:
        heuristic = OpponentBlockingHeuristic()
    elif heuristic_choice == 5:
        # For adaptive agent we don't use a single heuristic
        agent = AdaptiveMinimaxAgent(player, depth, None, use_alpha_beta)
    else:
        print("Unknown heuristic. Using default (Mobility difference).")
        heuristic = MobilityDifferenceHeuristic()

    # Create agent only if it's not adaptive (which has already been created)
    if heuristic_choice != 5:
        agent = MinimaxAgent(player, depth, heuristic, use_alpha_beta)



    return agent





if __name__ == "__main__":
    # Odczytaj parametry wejściowe
    print("Please enter board size (n m):")
    try:
        n, m = map(int, input().split())
        size = (n, m)
    except:
        print("Wrong format. Using default size 5x6.")
        size = (5, 6)

    print(f"Board size: {size[0]}x{size[1]}")


    print("\nDo you want to enter a custom start board? (t/n)")
    custom_board = input().lower() == 't'

    initial_board = None
    if custom_board:
        print(f"Provide board {size[0]}x{size[1]} (B - Black, W - White, _ - Null):")
        board = []
        for i in range(size[0]):
            row = input().split()
            if len(row) != size[1]:
                print(f"Error: row {i+1} has incorrect length. Using default board.")
                custom_board = False
                break
            board.append(row)

        if custom_board:
            initial_board = np.array(board)


    player = handle_players_agent_choice('B')
    opponent = handle_players_agent_choice('W')

    print("\nStarting the game...\n")
    final_game, result = play_game(player, opponent, initial_board, size)

    print("\nGame over!")
    print("Final board:")
    final_game.print_board()
    print(f"\nNumber of rounds: {result['rounds']}")
    print(f"Winner: {'Black (B)' if result['winner'] == 'B' else 'White (W)'}")





















