from abc import ABC, abstractmethod
import numpy as np


class ClobberHeuristic(ABC):
    """Interface"""

    @abstractmethod
    def evaluate(self, game, player):


        pass


class MobilityDifferenceHeuristic(ClobberHeuristic):
    """Difference in mobility between players"""

    def evaluate(self, game, player):
        opponent = 'W' if player == 'B' else 'B'
        player_moves = len(game.get_possible_moves(player))
        opponent_moves = len(game.get_possible_moves(opponent))
        return player_moves - opponent_moves


class PieceMobilityHeuristic(ClobberHeuristic):
    """Heuristics based on the number of mobile pieces"""

    def evaluate(self, game, player):
        mobile_pieces = set()
        for move in game.get_possible_moves(player):
            x1, y1, _, _ = move
            mobile_pieces.add((x1, y1))
        return len(mobile_pieces)


class CenterControlHeuristic(ClobberHeuristic):
    """Heuristics based on the control of the center positions"""

    def evaluate(self, game, player):
        center_i, center_j = game.size[0] // 2, game.size[1] // 2
        score = 0
        opponent = 'W' if player == 'B' else 'B'

        for i in range(game.size[0]):
            for j in range(game.size[1]):
                if game.board[i, j] == player:
                    # Distance from the center
                    distance = abs(i - center_i) + abs(j - center_j)
                    score += (game.size[0] + game.size[1]) - distance
                elif game.board[i, j] == opponent:  # Opponent
                    distance = abs(i - center_i) + abs(j - center_j)
                    score -= (game.size[0] + game.size[1]) - distance

        return score


class AdjacentOpponentHeuristic(ClobberHeuristic):
    """Heuristics based on the number of adjacent opponent pieces"""

    def evaluate(self, game, player):
        opponent = 'W' if player == 'B' else 'B'
        score = 0


        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for i in range(game.size[0]):
            for j in range(game.size[1]):
                if game.board[i, j] == player:
                    # Check adjacent positions for opponent pieces
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if (0 <= ni < game.size[0] and 0 <= nj < game.size[1] and
                                game.board[ni, nj] == opponent):
                            score += 1

        return score


class OpponentBlockingHeuristic(ClobberHeuristic):
    """Heuristics based on the number of opponent pieces that can be blocked"""


    def evaluate(self, game, player):
        opponent = 'W' if player == 'B' else 'B'
        player_moves = len(game.get_possible_moves(player))
        opponent_moves = len(game.get_possible_moves(opponent))

        if opponent_moves == 0:
            return float('inf')  # Wygrana
        elif player_moves == 0:
            return float('-inf')  # Przegrana
        else:
            return player_moves / (opponent_moves + 1)  # +1 for avoid division by zero


class AdaptiveHeuristic(ClobberHeuristic):
    """heuristics based on the game phase"""

    def __init__(self):
        self.mobility_diff = MobilityDifferenceHeuristic()
        self.center_control = CenterControlHeuristic()
        self.opponent_blocking = OpponentBlockingHeuristic()

    def evaluate(self, game, player):

        player_pieces = np.sum(game.board == player)
        opponent = 'W' if player == 'B' else 'B'
        opponent_pieces = np.sum(game.board == opponent)
        total_pieces = player_pieces + opponent_pieces


        initial_pieces = game.size[0] * game.size[1]
        if total_pieces > 0.7 * initial_pieces:  # Early phase
            return self.center_control.evaluate(game, player)
        elif total_pieces > 0.3 * initial_pieces:  # Mid phase
            return self.mobility_diff.evaluate(game, player)
        else:  # End phase
            return self.opponent_blocking.evaluate(game, player)