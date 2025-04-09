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
    def __init__(self, board_size=(5, 6), max_depth=3, use_alpha_beta=True, num_games=10):

        self.board_size = board_size
        self.max_depth = max_depth
        self.use_alpha_beta = use_alpha_beta
        self.num_games = num_games

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

    def play_games(self, black_heuristic, white_heuristic, num_games):
        """
        Play multiple games between two heuristics.

        Args:
            black_heuristic: Heuristic name for black player
            white_heuristic: Heuristic name for white player
            num_games: Number of games to play

        Returns:
            list: Results of all games
        """
        results = []
        for _ in range(num_games):
            # Create agents
            black_agent = self.create_agent('B', black_heuristic)
            white_agent = self.create_agent('W', white_heuristic)

            # Use the play_game function from ClobberGame
            _, result = play_game(
                agent1=black_agent,
                agent2=white_agent,
                size=self.board_size,
                max_rounds=100,  # Safety limit
                silent=True  # Suppress output for simulations
            )

            results.append(result)
        return results

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
        total_games = total_matchups * self.num_games
        print(f"Running {total_games} games across {total_matchups} matchups...")

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_threads) as executor:
            # Create a dictionary to store future objects and their corresponding matchups
            future_to_matchup = {}

            # Submit all tasks
            for black_h, white_h in matchups:
                future = executor.submit(self.play_games, black_h, white_h, self.num_games)
                future_to_matchup[future] = (black_h, white_h)

            # Process completed tasks with a progress bar
            with tqdm(total=total_matchups) as pbar:
                for future in concurrent.futures.as_completed(future_to_matchup):
                    matchup = future_to_matchup[future]
                    try:
                        results = future.result()
                        self.results[matchup] = results
                    except Exception as exc:
                        print(f"{matchup} generated an exception: {exc}")
                    pbar.update(1)

        # Calculate performance metrics
        self.calculate_performance_metrics()

    def calculate_performance_metrics(self):
        """Calculate performance metrics for all matchups."""
        for matchup, games in self.results.items():
            black_h, white_h = matchup
            black_wins = sum(1 for game in games if game["winner"] == "B")
            white_wins = sum(1 for game in games if game["winner"] == "W")
            avg_rounds = sum(game["rounds"] for game in games) / len(games)
            avg_nodes_black = sum(game["nodes_black"] for game in games) / len(games)
            avg_nodes_white = sum(game["nodes_white"] for game in games) / len(games)
            avg_time_black = sum(game["time_black"] for game in games) / len(games)
            avg_time_white = sum(game["time_white"] for game in games) / len(games)

            self.performance_metrics[matchup] = {
                "black_wins": black_wins,
                "white_wins": white_wins,
                "win_rate_black": black_wins / len(games),
                "win_rate_white": white_wins / len(games),
                "avg_rounds": avg_rounds,
                "avg_nodes_black": avg_nodes_black,
                "avg_nodes_white": avg_nodes_white,
                "avg_time_black": avg_time_black,
                "avg_time_white": avg_time_white
            }

    def generate_report(self, output_dir="simulation_results"):
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

        # Prepare data for win rate heatmap
        heuristic_names = list(self.heuristics.keys())
        win_rate_matrix = np.zeros((len(heuristic_names), len(heuristic_names)))

        for i, black_h in enumerate(heuristic_names):
            for j, white_h in enumerate(heuristic_names):
                matchup = (black_h, white_h)
                if matchup in self.performance_metrics:
                    win_rate_matrix[i, j] = self.performance_metrics[matchup]["win_rate_black"]

        # Create win rate heatmap
        plt.figure(figsize=(12, 10))
        plt.imshow(win_rate_matrix, cmap='RdYlGn', vmin=0, vmax=1)
        plt.colorbar(label='Black Win Rate')
        plt.xticks(np.arange(len(heuristic_names)), heuristic_names, rotation=45)
        plt.yticks(np.arange(len(heuristic_names)), heuristic_names)
        plt.xlabel('White Heuristic')
        plt.ylabel('Black Heuristic')
        plt.title('Black Win Rate by Heuristic Matchup')

        # Add text annotations
        for i in range(len(heuristic_names)):
            for j in range(len(heuristic_names)):
                text = f"{win_rate_matrix[i, j]:.2f}"
                plt.text(j, i, text, ha="center", va="center",
                         color="black" if 0.25 < win_rate_matrix[i, j] < 0.75 else "white")

        plt.tight_layout()
        plt.savefig(f"{output_dir}/win_rate_heatmap.png")

        # Create CSV report
        report_data = []
        for matchup, metrics in self.performance_metrics.items():
            black_h, white_h = matchup
            row = {
                "Black_Heuristic": black_h,
                "White_Heuristic": white_h,
                "Black_Wins": metrics["black_wins"],
                "White_Wins": metrics["white_wins"],
                "Black_Win_Rate": metrics["win_rate_black"],
                "White_Win_Rate": metrics["win_rate_white"],
                "Avg_Rounds": metrics["avg_rounds"],
                "Avg_Nodes_Black": metrics["avg_nodes_black"],
                "Avg_Nodes_White": metrics["avg_nodes_white"],
                "Avg_Time_Black": metrics["avg_time_black"],
                "Avg_Time_White": metrics["avg_time_white"]
            }
            report_data.append(row)

        df = pd.DataFrame(report_data)
        df.to_csv(f"{output_dir}/simulation_results.csv", index=False)

        # Generate summary statistics
        best_black = df.loc[df['Black_Win_Rate'].idxmax()]
        best_white = df.loc[df['White_Win_Rate'].idxmax()]
        most_efficient_black = df.loc[df[df['Black_Win_Rate'] > 0.5]['Avg_Nodes_Black'].idxmin()]
        most_efficient_white = df.loc[df[df['White_Win_Rate'] > 0.5]['Avg_Nodes_White'].idxmin()]

        with open(f"{output_dir}/summary.txt", 'w') as f:
            f.write("CLOBBER SIMULATION SUMMARY\n")
            f.write("=========================\n\n")
            f.write(f"Board Size: {self.board_size[0]}x{self.board_size[1]}\n")
            f.write(f"Max Depth: {self.max_depth}\n")
            f.write(f"Alpha-Beta Pruning: {'Enabled' if self.use_alpha_beta else 'Disabled'}\n")
            f.write(f"Games per Matchup: {self.num_games}\n\n")

            f.write("BEST PERFORMING HEURISTICS\n")
            f.write("-------------------------\n")
            f.write(f"Best Black Heuristic: {best_black['Black_Heuristic']} ")
            f.write(f"(Win Rate: {best_black['Black_Win_Rate']:.2f}) ")
            f.write(f"against {best_black['White_Heuristic']}\n")

            f.write(f"Best White Heuristic: {best_white['White_Heuristic']} ")
            f.write(f"(Win Rate: {best_white['White_Win_Rate']:.2f}) ")
            f.write(f"against {best_white['Black_Heuristic']}\n\n")

            f.write("MOST EFFICIENT HEURISTICS (winning with minimal node exploration)\n")
            f.write("------------------------------------------------------------\n")
            f.write(f"Most Efficient Black: {most_efficient_black['Black_Heuristic']} ")
            f.write(f"(Avg Nodes: {most_efficient_black['Avg_Nodes_Black']:.0f}, ")
            f.write(f"Win Rate: {most_efficient_black['Black_Win_Rate']:.2f})\n")

            f.write(f"Most Efficient White: {most_efficient_white['White_Heuristic']} ")
            f.write(f"(Avg Nodes: {most_efficient_white['Avg_Nodes_White']:.0f}, ")
            f.write(f"Win Rate: {most_efficient_white['White_Win_Rate']:.2f})\n\n")

            # Calculate overall heuristic performance
            f.write("OVERALL HEURISTIC PERFORMANCE\n")
            f.write("----------------------------\n")

            # Aggregate performance for each heuristic as black and white
            overall_stats = {}
            for h in heuristic_names:
                black_games = df[df['Black_Heuristic'] == h]
                white_games = df[df['White_Heuristic'] == h]

                overall_stats[h] = {
                    'black_win_rate': black_games['Black_Win_Rate'].mean(),
                    'white_win_rate': white_games['White_Win_Rate'].mean(),
                    'overall_win_rate': (black_games['Black_Win_Rate'].sum() +
                                         white_games['White_Win_Rate'].sum()) / (len(black_games) + len(white_games))
                }

            # Sort by overall win rate
            sorted_stats = sorted(overall_stats.items(), key=lambda x: x[1]['overall_win_rate'], reverse=True)

            for heuristic, stats in sorted_stats:
                f.write(f"{heuristic}:\n")
                f.write(f"  As Black: {stats['black_win_rate']:.2f} win rate\n")
                f.write(f"  As White: {stats['white_win_rate']:.2f} win rate\n")
                f.write(f"  Overall:  {stats['overall_win_rate']:.2f} win rate\n\n")

        print(f"Report generated in {output_dir}/ directory")


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

    print("\nNumber of games per matchup:")
    num_games = int(input() or "10")

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
        num_games=num_games
    )

    simulator.run_simulations(num_threads=num_threads, gpu=use_gpu)
    simulator.generate_report()