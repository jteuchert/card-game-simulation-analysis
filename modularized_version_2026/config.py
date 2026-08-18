from pathlib import Path

NUM_PLAYERS = 2 # Set to at least 2. More players result in longer games/longer simulation time.

JOKERS = True # Include 2 jokers in deck?
VALUES = 9 # 0 - 9: # of numeric values (cards) [9 = standard]

NUM_SIMULATIONS = 50_000_000


MAX_TURNS = 19999 # Stop simulation after this many turns
NUM_BINS = MAX_TURNS + 1 # bins from 0 to MAX_TURNS in steps of 1

BASE_DECK = ["A", "J", "Q", "K"] + [str(i) for i in range(2, 2+VALUES)]
FULL_DECK = BASE_DECK * 4 + ["Joker", "Joker"]*JOKERS

joker_str = "_" + "no_"*(not JOKERS) + "jokers"
VARIATION_TAG = f"{NUM_PLAYERS}p_{VALUES}_numeric_values{joker_str}"
RESULTS_FOLDER = "results_data"
PLOTS_FOLDER = "results_plots"
HISTOGRAM_FILE = Path(f"{RESULTS_FOLDER}/{VARIATION_TAG}_histogram.npz")
LOWEST_FILE = Path(f"{RESULTS_FOLDER}/{VARIATION_TAG}_lowest_turns.csv")
HIGHEST_FILE = Path(f"{RESULTS_FOLDER}/{VARIATION_TAG}_highest_turns.csv")

SIMS_PER_WORKER = 100_000 # max. 100_000

# Make sure the number of simulations can be divided into an integer number of workers
NUM_SIMULATIONS = (NUM_SIMULATIONS//SIMS_PER_WORKER)*SIMS_PER_WORKER