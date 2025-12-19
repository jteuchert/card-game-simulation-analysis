""" Script to simulate games in big numbers
Usage:
    - Configure setup below (NUM_BATCHES: How many batches of 1 million games each should be simulated
                             NUM_PLAYERS: number of players (don't change, more players are not yet fully supported)
                             END_RESULTS_FILE: file name for results, don't change)
                             MAX_TURNS: determines when the simulation ends in case it would run too long)
    - Optional: adjust number of used cores for parallel processing (l. 293)
    - Run script                       
"""

import random
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import os
import matplotlib.pyplot as plt
import json

# ---------------------------------------------------
# Config
# ---------------------------------------------------

NUM_BATCHES = 10
NUM_PLAYERS = 2
END_RESULTS_FILE = Path("end_result.csv")
MAX_TURNS = 9999

# ---------------------------------------------------

# Prepare deck
BASE_DECK = [str(i) for i in range(2, 11)] + ["A", "J", "Q", "K"]
FULL_DECK = 4 * BASE_DECK + ["Joker", "Joker"]


# ---------------------------------------------------
# Setup summary and results file if missing
# ---------------------------------------------------
def prepare_summary_file():
    if not summary_file.exists():
        cols = ["id", "turns", "winner", "hand_0", "hand_1"]
        if NUM_PLAYERS == 3:
            cols.append("hand_2")
        pd.DataFrame(columns=cols).to_csv(summary_file, index=False)
        
        
def prepare_results_file():
    if not END_RESULTS_FILE.exists():
        cols = ["batch", "shortest", "longest", "player 0 win rate", "bins", "counts"]
        pd.DataFrame(columns=cols).to_csv(END_RESULTS_FILE, index=False)


# ---------------------------------------------------
# Game simulation
# ---------------------------------------------------
def simulate_game(game_id, start_hands):
    """ Simulate one game, return summary """
    hands = [h.copy() for h in start_hands]
    desk = []
    turn = 0
    player = 0

    while turn < MAX_TURNS:
        # skip 3p empty player
        if NUM_PLAYERS == 3 and not hands[player]:
            player = (player + 1) % NUM_PLAYERS
            continue

        # win?
        if sum(1 for h in hands if len(h) == 0) > NUM_PLAYERS - 2:
            break

        # play a card
        card = hands[player].pop(0)
        desk.append(card)

        # check match
        if len(desk) != len(set(desk)):
            matching_card = desk[-1]
            idx = desk.index(matching_card)
            gain = desk[idx:]
            del desk[idx:]
            hands[player].extend(gain)
        else:
            player = (player + 1) % NUM_PLAYERS

        turn += 1

    summary = {
        "id": game_id,
        "turns": turn,
        "winner": player,
        "initial_hands": start_hands
    }
    return summary


# ---------------------------------------------------
# Summary writing
# ---------------------------------------------------
def append_summary(summaries):
    df_rows = []
    for s in summaries:
        row = {
            "id": s["id"],
            "turns": s["turns"],
            "winner": s["winner"],
            "hand_0": ", ".join(s["initial_hands"][0]),
            "hand_1": ", ".join(s["initial_hands"][1]),
        }
        if NUM_PLAYERS == 3:
            row["hand_2"] = ", ".join(s["initial_hands"][2])
        df_rows.append(row)

    pd.DataFrame(df_rows).to_csv(summary_file, mode="a", header=False, index=False)


# ---------------------------------------------------
# Results writing
# ---------------------------------------------------
def append_result(batch, shortest, longest, win_rate_p0, bins, counts):
    row = {
        "batch": batch,
        "shortest": shortest,
        "longest": longest,
        "player 0 win rate": win_rate_p0,
        "bins": json.dumps(bins.tolist()),
        "counts": json.dumps(counts.tolist()),
    }
    df = pd.DataFrame([row])
    df.to_csv(END_RESULTS_FILE, mode="a", header=False, index=False)


# ---------------------------------------------------
# Parallel execution
# ---------------------------------------------------
def run_parallel_simulations(n_games, max_workers=None):
    prepare_summary_file()
    summary_df = pd.read_csv(summary_file)
    start_index = len(summary_df)

    tasks = []

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        for i in range(n_games):
            game_id = start_index + i
            deck = FULL_DECK.copy()
            random.shuffle(deck)
            hands = [[] for _ in range(NUM_PLAYERS)]
            for j, card in enumerate(deck):
                hands[j % NUM_PLAYERS].append(card)

            tasks.append(ex.submit(simulate_game, game_id, hands))

        results = [t.result() for t in tasks]

    # write summary
    append_summary(results)

# ---------------------------------------------------
# Plotting functions
# ---------------------------------------------------
def turn_count_plot(batch, win_rate_p0):
    """ Plot the distribution of turn counts for all games of a batch. """
    df = pd.read_csv(summary_file)

    turn_counts = df["turns"].tolist()
    if not turn_counts:
        print("[Warning] No games found to plot.")
        return

    min_turns = min(turn_counts)
    max_turns = max(turn_counts)
    mean_turns = sum(turn_counts) / len(turn_counts)

    # Plot histogram
    plt.figure(figsize=(8, 5), dpi=300)
    counts, bins, _ = plt.hist(turn_counts, bins=[100*w for w in range(100)], edgecolor="black", alpha=0.7, label=f"Min: {min_turns}, Max: {max_turns}")
    plt.title(f"Distribution of Game Lengths Batch {batch}")
    plt.xlabel("Number of Turns")
    plt.ylabel("Number of Games")
    plt.grid(True, linestyle="--", alpha=0.5)

    # Mean line
    plt.axvline(mean_turns, color='red', linestyle='--', label=f"Mean = {mean_turns:.0f}")

    # peak line
    max_bin_index = counts.argmax()
    peak_x = (bins[max_bin_index] + bins[max_bin_index + 1]) / 2
    plt.axvline(peak_x, color='orange', linestyle='-.', label=f"Peak # turns = {peak_x:.0f}")

    plt.plot([], [], ' ', label=f"{len(turn_counts)} games")
    plt.legend()
    
    #max_y = counts.max()
    #plt.xlim(0, 1.1*max_turns)
    #plt.ylim(0, 1.1*max_y)
    plt.yscale("log")
    
    plt.tight_layout()
    plt.savefig(f"turn_count_batch_{batch}.png", dpi=300, bbox_inches="tight")
    plt.show()
    
    append_result(batch, min_turns, max_turns, win_rate_p0, bins, counts)


def analyse_batch(batch):
    df = pd.read_csv(summary_file)

    # Win rates
    win_rates = df["winner"].value_counts(normalize=True).sort_index()
    print("\n=== Win Rates ===")
    for p in range(NUM_PLAYERS):
        print(f"Player {p}: {win_rates.get(p, 0):.2%}")

    # Basic stats
    min_id = df["turns"].idxmin()
    max_id = df["turns"].idxmax()
    
    min_val = df.iloc[min_id]["turns"]
    max_val = df.iloc[max_id]["turns"]
    
    shortest_game_id = df.iloc[min_id]["id"]
    longest_game_id = df.iloc[max_id]["id"]

    print(f"\nShortest game: ID={shortest_game_id}, turns={min_val}")
    print(f"Longest game:  ID={longest_game_id}, turns={max_val}")
    print(f"Average length: {df['turns'].mean():.2f}")

    # Plot: Turn count distribution
    print("\nPlotting turn count distribution...")
    turn_count_plot(batch, win_rates.get(0, 0))

# ---------------------------------------------------
# Analysis functions
# ---------------------------------------------------
def analyze_batches():
    end_results = pd.read_csv(END_RESULTS_FILE)
    num_saved_batches = len(end_results.index)
    globally_shortest = end_results["shortest"].min()
    globally_longest = end_results["longest"].max()
    global_win_rate_p0 = end_results["player 0 win rate"].mean()

    end_results["bins"] = end_results["bins"].apply(json.loads)
    end_results["counts"] = end_results["counts"].apply(json.loads)
    
    global_bins = end_results.iloc[0]["bins"] # assuming the bins are the same for all batches
    global_bins = np.array(global_bins)
    
    counts_array = np.array(end_results["counts"].tolist())
    global_counts = np.sum(counts_array, axis=0)

    print("\n=== Final Win Rates ===")
    print(f"Player 0: {global_win_rate_p0:.2%}")
    print(f"Player 1: {1 - global_win_rate_p0:.2%}")
    
    # Final plot
    # Calculate bin centers
    bin_centers = (global_bins[:-1] + global_bins[1:]) / 2

    plt.figure(figsize=(8, 5), dpi=300)
    plt.bar(bin_centers, global_counts, width=np.diff(global_bins), edgecolor="black", alpha=0.7, label=f"Min: {globally_shortest}, Max: {globally_longest}")
    plt.xlabel("Number of Turns")
    plt.ylabel("Number of Games")
    plt.title("Distribution of Game Lengths")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.plot([], [], ' ', label=f"{num_saved_batches} million games")
    plt.legend()
    
    #max_y = counts.max()
    #plt.xlim(0, 1.1*max_turns)
    #plt.ylim(1, 2*max_y)
    plt.yscale("log")
    
    plt.tight_layout()
    plt.savefig("turn_count_final.png", dpi=300, bbox_inches="tight")
    plt.show()
    

# ---------------------------------------------------
# Execution
# ---------------------------------------------------
if __name__ == "__main__":
    print("Initializing...")
    prepare_results_file()
    df = pd.read_csv(END_RESULTS_FILE)
    num_existing_batches = len(df.index)
    print(f"Number of existing batches: {num_existing_batches}")
    summary_file = Path(f"summary_batch_{num_existing_batches}.csv")
    
    max_workers = os.cpu_count() - 1 # Use all cores but leave 1 free
    for b in range(NUM_BATCHES):
        batch = b + num_existing_batches
        print(f"Starting batch id {batch}...")
        summary_file = Path(f"summary_batch_{batch}.csv")
        for p in range(10):
            run_parallel_simulations(100000, max_workers=max_workers)
            print(f"{(p+1)*100000} simulations of batch {batch} done.")
        analyse_batch(batch)   
        print(f"Batch {batch} done.")
    print("Analyzing summary files...")
    analyze_batches()
    print("All done.")
