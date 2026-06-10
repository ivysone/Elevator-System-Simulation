# calculate_winner_percentages.py

def calculate_percentages(file_path="winners.txt"):
    # Initialize counters
    winners_count = {"LOOK": 0, "SCAN": 0, "Efficiency": 0}
    total_runs = 0

    # Read the file
    try:
        with open(file_path, "r") as file:
            for line in file:
                winner = line.strip()
                if winner in winners_count:
                    winners_count[winner] += 1
                    total_runs += 1
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please run the test script first.")
        return

    if total_runs == 0:
        print("No data found in winners.txt.")
        return

    # Calculate and print percentages
    print(f"\nTotal Runs: {total_runs}")
    print("Winning Percentages:")
    for algo, count in winners_count.items():
        percentage = (count / total_runs) * 100
        print(f"{algo}: {percentage:.2f}% ({count} wins)")

    # Determine the overall winner
    max_wins = max(winners_count.values())
    overall_winners = [algo for algo, count in winners_count.items() if count == max_wins]
    if len(overall_winners) > 1:
        print(f"Tie for most wins: {', '.join(overall_winners)} with {max_wins} wins each")
    else:
        print(f"Overall winner: {overall_winners[0]} with {max_wins} wins")

if __name__ == "__main__":
    calculate_percentages()