
from ClobberHeuristic import *
class MinimaxAgent:
    def __init__(self,player, max_depth=3, heuristic=None, use_alpha_beta=True):

        self.max_depth = max_depth
        self.player = player
        self.opponent = 'W' if player == 'B' else 'B'

        self.heuristic = heuristic

        self.use_alpha_beta = use_alpha_beta
        self.nodes_visited = 0

    def get_move(self, game):

        self.nodes_visited = 0

        if self.use_alpha_beta:
            best_value, best_move = self.alpha_beta(game, self.max_depth,
                                                    float('-inf'), float('inf'), True)
        else:
            best_value, best_move = self.minimax(game, self.max_depth, True)

        return best_move

    def minimax(self, game, depth, is_maximizing):
        #print(f"minimax, depth: {depth}, nodes: {self.nodes_visited}")

        self.nodes_visited += 1



        if depth == 0 or game.is_game_over():
            return game.evaluate(self.player, self.heuristic), None

        current_player = self.player if is_maximizing else self.opponent
        possible_moves = game.get_possible_moves(current_player)


        if not possible_moves:

            if game.get_possible_moves(self.opponent if is_maximizing else self.player):

                return self.minimax(game, depth, not is_maximizing)
            else:
                # Gra zakończona
                return game.evaluate(self.player, self.heuristic), None

        best_move = None
        if is_maximizing:
            best_value = float('-inf')
            for move in possible_moves:
                new_game = game.make_move(move)
                value, _ = self.minimax(new_game, depth - 1, False)

                if value > best_value:
                    best_value = value
                    best_move = move
        else:
            best_value = float('inf')
            for move in possible_moves:
                new_game = game.make_move(move)
                value, _ = self.minimax(new_game, depth - 1, True)

                if value < best_value:
                    best_value = value
                    best_move = move

        return best_value, best_move

    def alpha_beta(self, game, depth, alpha, beta, is_maximizing):

        self.nodes_visited += 1


        if depth == 0 or game.is_game_over():
            return game.evaluate(self.player, self.heuristic), None

        current_player = self.player if is_maximizing else self.opponent
        possible_moves = game.get_possible_moves(current_player)


        if not possible_moves:

            other_player_moves = game.get_possible_moves(self.opponent if is_maximizing else self.player)
            if other_player_moves:

                return self.alpha_beta(game, depth, alpha, beta, not is_maximizing)
            else:

                return game.evaluate(self.player, self.heuristic), None

        best_move = None
        if is_maximizing:
            best_value = float('-inf')
            for move in possible_moves:
                new_game = game.make_move(move)
                value, _ = self.alpha_beta(new_game, depth - 1, alpha, beta, False)

                if value > best_value:
                    best_value = value
                    best_move = move

                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break  # pruning beta
        else:
            best_value = float('inf')
            for move in possible_moves:
                new_game = game.make_move(move)
                value, _ = self.alpha_beta(new_game, depth - 1, alpha, beta, True)

                if value < best_value:
                    best_value = value
                    best_move = move

                beta = min(beta, best_value)
                if beta <= alpha:
                    break  # pruning alfa

        return best_value, best_move







class AdaptiveMinimaxAgent(MinimaxAgent):


    def __init__(self, player, max_depth=3, heuristics=None, use_alpha_beta=True):

        # Default heuristics if none provided
        if heuristics is None:
            self.heuristics = [
                MobilityDifferenceHeuristic(),
                PieceMobilityHeuristic(),
                CenterControlHeuristic(),
                AdjacentOpponentHeuristic(),
                OpponentBlockingHeuristic()
            ]
        else:
            self.heuristics = heuristics


        super().__init__(player, max_depth, self.heuristics[0], use_alpha_beta)

        self.last_moves = []
        self.opponent_patterns = {}

    def get_move(self, game):

        # Choose heuristic based on game state and opponent history
        self.heuristic = self.choose_heuristic(game)

        # Use standard Minimax method to find the best move
        return super().get_move(game)

    def choose_heuristic(self, game):


        player_pieces = np.sum(game.board == self.player)
        opponent_pieces = np.sum(game.board == self.opponent)
        total_pieces = player_pieces + opponent_pieces


        total_spaces = game.size[0] * game.size[1]
        board_fullness = total_pieces / total_spaces


        if len(self.last_moves) >= 3:
            self.analyze_opponent_patterns(game)


        if board_fullness > 0.7:  # Early game phase
            # Center control is good at the beginning
            return self.heuristics[2]  # CenterControlHeuristic
        elif board_fullness > 0.4:  # Middle game phase
            # Check if opponent prefers specific move patterns
            if self.opponent_patterns:
                most_common_pattern = max(self.opponent_patterns.items(),
                                          key=lambda x: x[1])[0]

                # Counter detected patterns
                if most_common_pattern == "aggressive":
                    # If opponent is aggressive, choose defensive heuristic
                    return self.heuristics[4]  # OpponentBlockingHeuristic
                elif most_common_pattern == "defensive":
                    # If opponent is defensive, choose offensive heuristic
                    return self.heuristics[3]  # AdjacentOpponentHeuristic
                elif most_common_pattern == "central":
                    # If opponent focuses on center, choose mobility control
                    return self.heuristics[1]  # PieceMobilityHeuristic

            # Default strategy for middle phase
            return self.heuristics[0]  # MobilityDifferenceHeuristic
        else:  # End game phase
            # In end game, blocking opponent is most important
            return self.heuristics[4]  # OpponentBlockingHeuristic

    def analyze_opponent_patterns(self, game):
        """Analyze patterns in recent opponent moves."""
        # Reset patterns
        self.opponent_patterns = {
            "aggressive": 0,
            "defensive": 0,
            "central": 0
        }

        # Analyze recent moves
        for move in self.last_moves[-3:]:
            x1, y1, x2, y2 = move

            # Distance from board center
            center_i, center_j = game.size[0] // 2, game.size[1] // 2
            distance_from_center = abs(x2 - center_i) + abs(y2 - center_j)

            # Classify the move
            if distance_from_center <= 2:
                # Move toward center
                self.opponent_patterns["central"] += 1

            # Check if move is aggressive (leads to many capture options)
            if self.is_aggressive_move(game, move):
                self.opponent_patterns["aggressive"] += 1

            # Check if move is defensive (protects own pieces)
            if self.is_defensive_move(game, move):
                self.opponent_patterns["defensive"] += 1

    def is_aggressive_move(self, game, move):
        """Check if move is aggressive (creates more capture opportunities)."""
        x1, y1, x2, y2 = move

        # Simulate making the move
        new_game = game.make_move(move)

        # Check if new move creates more move opportunities
        old_moves = len(game.get_possible_moves(self.opponent))
        new_moves = len(new_game.get_possible_moves(self.opponent))

        return new_moves > old_moves + 1  # +1 is aggression threshold

    def is_defensive_move(self, game, move):


        # Simulate making the move
        new_game = game.make_move(move)

        # Check if new move reduces number of threatened pieces
        old_vulnerable = self.count_vulnerable_pieces(game, self.opponent)
        new_vulnerable = self.count_vulnerable_pieces(new_game, self.opponent)

        return new_vulnerable < old_vulnerable

    def count_vulnerable_pieces(self, game, player):
        """Count the number of vulnerable pieces for a player."""
        opponent = 'W' if player == 'B' else 'B'
        vulnerable_count = 0

        # Movement directions (up, down, left, right)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for i in range(game.size[0]):
            for j in range(game.size[1]):
                if game.board[i, j] == player:
                    # Check if any opponent piece can capture this piece
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if (0 <= ni < game.size[0] and 0 <= nj < game.size[1] and
                                game.board[ni, nj] == opponent):
                            vulnerable_count += 1
                            break  # If piece is vulnerable, don't count it multiple times

        return vulnerable_count

    def register_opponent_move(self, move):
        """Register opponent's move for pattern analysis."""
        self.last_moves.append(move)
        # Keep only the last N moves
        if len(self.last_moves) > 10:
            self.last_moves.pop(0)




