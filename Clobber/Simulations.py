import numpy as np
import time
import concurrent.futures
from Clobber import play_game
from ClobberHeuristic import *
from MinimaxAgent import MinimaxAgent, AdaptiveMinimaxAgent
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import os


class Simulation:
    def __init__(self, board_size=(5, 6), max_depth=3, use_alpha_beta=True):

        self.board_size = board_size
        self.max_depth = max_depth
        self.use_alpha_beta = use_alpha_beta


        # Define all available heuristics
        self.heuristics = {
            "MobilityDifference": MobilityDifferenceHeuristic(),
            "PieceMobility": PieceMobilityHeuristic(),
            "CenterControl": CenterControlHeuristic(),
            "AdjacentOpponent": AdjacentOpponentHeuristic(),
            "OpponentBlocking": OpponentBlockingHeuristic(),
            "Adaptive": "Adaptive"  # Special case for adaptive agent
        }

        # Initialize results storage
        self.results = {}
        self.performance_metrics = {}

    def create_agent(self, player, heuristic_name):

        if heuristic_name == "Adaptive":
            return AdaptiveMinimaxAgent(
                player=player,
                max_depth=self.max_depth,
                heuristics=None,  # Use default heuristics
                use_alpha_beta=self.use_alpha_beta
            )
        else:
            return MinimaxAgent(
                player=player,
                max_depth=self.max_depth,
                heuristic=self.heuristics[heuristic_name],
                use_alpha_beta=self.use_alpha_beta
            )

    def play_games(self, black_heuristic, white_heuristic):
        """
        Play multiple games between two heuristics.

        Args:
            black_heuristic: Heuristic name for black player
            white_heuristic: Heuristic name for white player
            num_games: Number of games to play

        Returns:
            list: Results of all games
        """


        # Create agents
        black_agent = self.create_agent('B', black_heuristic)
        white_agent = self.create_agent('W', white_heuristic)

        # Use the play_game function from ClobberGame
        _, result = play_game(
            agent1=black_agent,
            agent2=white_agent,
            size=self.board_size,
            max_rounds=100,  # Safety limit
            silent=True)  # Suppress output for simulations



        return result

    def run_simulations(self, num_threads=None, gpu=False):
        """
        Run simulations for all heuristic combinations.

        Args:
            num_threads: Number of threads to use. If None, uses CPU count.
            gpu: Whether to use GPU acceleration (currently not implemented)
        """
        if gpu:
            print("Note: GPU acceleration requested but not implemented. Using CPU.")

        # Create all possible heuristic matchups
        matchups = []
        for black_h in self.heuristics.keys():
            for white_h in self.heuristics.keys():
                matchups.append((black_h, white_h))

        # Progress display
        total_matchups = len(matchups)
        total_games = total_matchups
        print(f"Running {total_games} games across {total_matchups} matchups...")

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
            # Create a dictionary to store future objects and their corresponding matchups
            future_to_matchup = {}

            # Submit all tasks
            for black_h, white_h in matchups:
                future = executor.submit(self.play_games, black_h, white_h)
                future_to_matchup[future] = (black_h, white_h)

            # Process completed tasks with a progress bar
            with tqdm(total=total_matchups) as pbar:
                for future in concurrent.futures.as_completed(future_to_matchup):
                    matchup = future_to_matchup[future]
                    try:
                        result = future.result()
                        self.results[matchup] = result
                    except Exception as exc:
                        print(f"{matchup} generated an exception: {exc}")
                    pbar.update(1)

        # Calculate performance metrics
        self.calculate_performance_metrics()

    def calculate_performance_metrics(self):
        """Calculate performance metrics for all matchups."""
        for matchup, game in self.results.items():
            black_h, white_h = matchup
            black_won = 1 if game["winner"] == "B" else 0
            rounds = game["rounds"]
            nodes_black = game["nodes_black"]
            nodes_white = game["nodes_white"]
            time_black = game["time_black"]
            time_white = game["time_white"]

            self.performance_metrics[matchup] = {
                "black_won": black_won,
                "rounds": rounds,
                "nodes_black": nodes_black,
                "nodes_white": nodes_white,
                "time_black": time_black,
                "time_white": time_white
            }

    def generate_report(self ,output_dir="simulation_results"):
        """
        Generate detailed report of simulation results.

        Args:
            output_dir: Directory to save report files
        """
        if not self.performance_metrics:
            print("No performance metrics available. Run simulations first.")
            return

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        final_dir = f"{output_dir}/max_depth_{self.max_depth}/alpha_beta_{self.use_alpha_beta}"
        os.makedirs(final_dir, exist_ok=True)



        # Prepare data for win rate heatmap
        heuristic_names = list(self.heuristics.keys())
        win_black_matrix = np.zeros((len(heuristic_names), len(heuristic_names)))

        for i, black_h in enumerate(heuristic_names):
            for j, white_h in enumerate(heuristic_names):
                matchup = (black_h, white_h)
                if matchup in self.performance_metrics:
                    win_black_matrix[i, j] = self.performance_metrics[matchup]["black_won"]

        # Create win rate heatmap
        plt.figure(figsize=(12, 10))
        plt.imshow(win_black_matrix, cmap='RdYlGn', vmin=0, vmax=1)
        plt.colorbar(label='Black Win Rate')
        plt.xticks(np.arange(len(heuristic_names)), heuristic_names, rotation=45)
        plt.yticks(np.arange(len(heuristic_names)), heuristic_names)
        plt.xlabel('White Heuristic')
        plt.ylabel('Black Heuristic')
        plt.title('Black Wins by Heuristic Matchup')

        # Add text annotations
        for i in range(len(heuristic_names)):
            for j in range(len(heuristic_names)):
                text = f"{win_black_matrix[i, j]:.2f}"
                plt.text(j, i, text, ha="center", va="center",
                         color="black" if 0.25 < win_black_matrix[i, j] < 0.75 else "white")

        plt.tight_layout()
        plt.savefig(f"{final_dir}/win_rate_heatmap.png")

        # Create CSV report
        report_data = []
        for matchup, metrics in self.performance_metrics.items():
            black_h, white_h = matchup
            row = {
                "Black_Heuristic": black_h,
                "White_Heuristic": white_h,
                "Black Won": metrics["black_won"],
                "Rounds": metrics["rounds"],
                "Nodes_Black": metrics["nodes_black"],
                "Nodes_White": metrics["nodes_white"],
                "Time_Black": metrics["time_black"],
                "Time_White": metrics["time_white"]
            }
            report_data.append(row)

        df = pd.DataFrame(report_data)
        df.to_csv(f"{final_dir}/simulation_results.csv", index=False)

        # Calculate strategy performance metrics
        # For Black player
        black_wins_by_strategy = {}
        for h in heuristic_names:
            wins = 0
            games = 0
            for white_h in heuristic_names:
                matchup = (h, white_h)
                if matchup in self.performance_metrics:
                    wins += self.performance_metrics[matchup]["black_won"]
                    games += 1
            if games > 0:
                black_wins_by_strategy[h] = wins / games

        # For White player
        white_wins_by_strategy = {}
        for h in heuristic_names:
            wins = 0
            games = 0
            for black_h in heuristic_names:
                matchup = (black_h, h)
                if matchup in self.performance_metrics:
                    # White wins when Black loses
                    wins += (1 - self.performance_metrics[matchup]["black_won"])
                    games += 1
            if games > 0:
                white_wins_by_strategy[h] = wins / games

        # Add overall best strategy recommendation
        overall_wins = {}

        #Calculate overall nodes and time
        all_nodes = 0
        all_time = 0
        for h in heuristic_names:
            overall_wins[h] = (black_wins_by_strategy.get(h, 0) + white_wins_by_strategy.get(h, 0)) / 2

        # Find best and worst strategies
        best_black = max(black_wins_by_strategy.items(), key=lambda x: x[1])
        worst_black = min(black_wins_by_strategy.items(), key=lambda x: x[1])
        best_white = max(white_wins_by_strategy.items(), key=lambda x: x[1])
        worst_white = min(white_wins_by_strategy.items(), key=lambda x: x[1])
        best_overall = max(overall_wins.items(), key=lambda x: x[1])
        worst_overall = min(overall_wins.items(), key=lambda x: x[1])
        # Add efficiency metrics (nodes per second)
        efficiency_by_strategy = {}
        for h in heuristic_names:
            black_nodes = 0
            black_time = 0
            white_nodes = 0
            white_time = 0
            games_as_black = 0
            games_as_white = 0

            # When playing as Black
            for white_h in heuristic_names:
                matchup = (h, white_h)
                if matchup in self.performance_metrics:
                    black_nodes += self.performance_metrics[matchup]["nodes_black"]
                    black_time += self.performance_metrics[matchup]["time_black"]
                    games_as_black += 1

            # When playing as White
            for black_h in heuristic_names:
                matchup = (black_h, h)
                if matchup in self.performance_metrics:
                    white_nodes += self.performance_metrics[matchup]["nodes_white"]
                    white_time += self.performance_metrics[matchup]["time_white"]
                    games_as_white += 1

            # Calculate efficiency (avoid division by zero)
            black_efficiency = black_nodes / black_time if black_time > 0 and games_as_black > 0 else 0
            white_efficiency = white_nodes / white_time if white_time > 0 and games_as_white > 0 else 0

            # Calculate all nodes and time
            all_nodes_h = black_nodes + white_nodes
            all_nodes +=all_nodes_h

            all_time_h = black_time + white_time
            all_time +=all_time_h









            # Average efficiency across both colors
            efficiency_by_strategy[h] = (
                                                    black_efficiency + white_efficiency) / 2 if games_as_black > 0 and games_as_white > 0 else 0

        most_efficient = max(efficiency_by_strategy.items(), key=lambda x: x[1])
        least_efficient = min(efficiency_by_strategy.items(), key=lambda x: x[1])

        # Calculate average nodes and time
        avg_nodes = all_nodes / len(self.performance_metrics)
        avg_time = all_time / len(self.performance_metrics)

        # Write summary file with strategy analysis
        with open(f"{final_dir}/summary.txt", 'w') as f:
            f.write("CLOBBER SIMULATION SUMMARY\n")
            f.write("=========================\n\n")
            f.write(f"Board Size: {self.board_size[0]}x{self.board_size[1]}\n")
            f.write(f"Max Depth: {self.max_depth}\n")
            f.write(f"Alpha-Beta Pruning: {'Enabled' if self.use_alpha_beta else 'Disabled'}\n")
            f.write(f"Nodes visited:{all_nodes}\n")
            f.write(f"Time elapsed:{all_time}\n")
            f.write(f" Average Nodes visited:{avg_nodes}\n")
            f.write(f"Average Time elapsed:{avg_time}\n")

            f.write("STRATEGY ANALYSIS\n")
            f.write("=================\n\n")

            f.write("Best Strategies:\n")
            f.write(f"- Best for Black: {best_black[0]} (Win rate: {best_black[1]:.2f})\n")
            f.write(f"- Best for White: {best_white[0]} (Win rate: {best_white[1]:.2f})\n\n")
            f.write(f"- Overall: {best_overall[0]} (Win rate: {best_overall[1]:.2f})\n\n")

            f.write("Worst Strategies:\n")
            f.write(f"- Worst for Black: {worst_black[0]} (Win rate: {worst_black[1]:.2f})\n")
            f.write(f"- Worst for White: {worst_white[0]} (Win rate: {worst_white[1]:.2f})\n\n")
            f.write(f"- Overall: {worst_overall[0]} (Win rate: {worst_overall[1]:.2f})\n\n")

            f.write("Computational Efficiency:\n")
            f.write(f"- Most Efficient: {most_efficient[0]} ({most_efficient[1]:.2f} nodes/second)\n")
            f.write(f"- Least Efficient: {least_efficient[0]} ({least_efficient[1]:.2f} nodes/second)\n\n")




            # Add overall best strategy recommendation
            overall_wins = {}
            for h in heuristic_names:
                overall_wins[h] = (black_wins_by_strategy.get(h, 0) + white_wins_by_strategy.get(h, 0)) / 2

            best_overall = max(overall_wins.items(), key=lambda x: x[1])
            f.write("OVERALL RECOMMENDATION:\n")
            f.write(
                f"The best overall strategy is {best_overall[0]} with an average win rate of {best_overall[1]:.2f}\n")

        print(f"Report generated in {final_dir}/ directory")


if __name__ == "__main__":
    print("Clobber Simulation Tool")
    print("======================")

    # Get simulation parameters
    print("\nBoard size (n m):")
    try:
        n, m = map(int, input().split())
        board_size = (n, m)
    except:
        print("Using default size 5x6")
        board_size = (5, 6)

    print("\nMax search depth (3-4 recommended):")
    max_depth = int(input() or "3")

    print("\nUse alpha-beta pruning? (y/n):")
    use_alpha_beta = input().lower() != 'n'



    print("\nNumber of threads (leave empty for auto):")
    try:
        num_threads = int(input())
    except:
        num_threads = None
        print("Using automatic thread count")

    print("\nUse GPU acceleration? (y/n):")
    use_gpu = input().lower() == 'y'

    # Create and run simulation
    simulator = Simulation(
        board_size=board_size,
        max_depth=max_depth,
        use_alpha_beta=use_alpha_beta,
    )

    simulator.run_simulations(num_threads=num_threads, gpu=use_gpu)
    simulator.generate_report()