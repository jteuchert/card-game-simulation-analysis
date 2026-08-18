import pandas as pd
import numpy as np


# ---------------------------
# File preparation functions
# ---------------------------

def prepare_hist_file(histogram_file, num_bins, num_players):
    """ Prepare histogram file (storing turn count histogram data) if missing. """
    if not histogram_file.exists():
        np.savez(
            histogram_file,
            num_sims=0,
            hist=np.zeros(num_bins, dtype=np.uint64),
            wins=np.zeros(num_players, dtype=np.uint64),
        )


def prepare_lowest_highest_files(num_players, lowest_file_path, highest_file_path):
    LOWEST_HIGHEST_COLUMNS = ["num_sims"] + [f"hand_{pn}" for pn in range(num_players)] + ["turn_count", "winner_idx"]
    if not lowest_file_path.exists():
        pd.DataFrame(columns=LOWEST_HIGHEST_COLUMNS).to_csv(lowest_file_path, index=False)
        
    if not highest_file_path.exists():
        pd.DataFrame(columns=LOWEST_HIGHEST_COLUMNS).to_csv(highest_file_path, index=False)


# ----------------------
# Data saving functions
# ----------------------

def save_histogram_data(num_sims, histogram_file, hist, wins):
    """ Save histogram data. """
    np.savez(
        histogram_file,
        num_sims=num_sims,
        hist=hist,
        wins=wins,
    )

def save_new_lowest_highest(file_path, num_sims, hands, turn_count, winner):
    df = pd.read_csv(file_path)
    
    row = (
        [num_sims]
        + [", ".join(hand) for hand in hands]
        + [turn_count, winner]
    )

    new_row = pd.DataFrame([row], columns=df.columns)
    new_row.to_csv(file_path, mode="a", header=False, index=False)

# -----------------------
# Data reading functions
# -----------------------

def get_lowest_highest_turn_counts(lowest_file, highest_file, max_turns):
    """ Read lowest and highest turn counts from files. """
    lowest_turns = max_turns
    highest_turns = 0

    if lowest_file.exists():
        df = pd.read_csv(lowest_file)
        if df.empty:
            print("No data yet.")
        else:
            last_row = df.iloc[-1]
            lowest_turns = last_row["turn_count"]
        
    if highest_file.exists():
        df = pd.read_csv(highest_file)
        if df.empty:
            print("No data yet.")
        else:
            last_row = df.iloc[-1]
            highest_turns = last_row["turn_count"]

    return lowest_turns, highest_turns

def get_lowest_highest_evolution(lowest_file, highest_file):
    if lowest_file.exists():
        df = pd.read_csv(lowest_file)
        if df.empty:
            print("No data yet.")
        else:
            lowest_evol = {
                "num_sims": df["num_sims"].tolist(),
                "turns": df["turn_count"].tolist(),
                "winner": df["winner_idx"].tolist(),
            }
        
    if highest_file.exists():
        df = pd.read_csv(highest_file)
        if df.empty:
            print("No data yet.")
        else:
            highest_evol = {
                "num_sims": df["num_sims"].tolist(),
                "turns": df["turn_count"].tolist(),
                "winner": df["winner_idx"].tolist(),
            }
    return lowest_evol, highest_evol


def get_num_of_simulations(histogram_file):
    """ Get the number of simulations from the histogram file. """
    if histogram_file.exists():
        hist_data = np.load(histogram_file)
        num_sims = int(hist_data["num_sims"])
        return num_sims
    else:
        return 0


def get_histogram_data(histogram_file, num_bins):
    """ Get histogram data from the histogram file. """
    if histogram_file.exists():
        hist_data = np.load(histogram_file)
        return hist_data["hist"]
    else:
        return np.zeros(num_bins, dtype=np.uint64)


def get_winner_counts(histogram_file, num_players):
    """ Get winner counts from the histogram file. """
    if histogram_file.exists():
        hist_data = np.load(histogram_file)
        win_counts = hist_data["wins"]
        return win_counts
    else:
        return np.zeros(num_players, dtype=np.uint64)

