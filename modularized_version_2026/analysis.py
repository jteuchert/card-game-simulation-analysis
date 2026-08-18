import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

from config import NUM_PLAYERS, MAX_TURNS, NUM_BINS, HISTOGRAM_FILE, HIGHEST_FILE, LOWEST_FILE, VARIATION_TAG, PLOTS_FOLDER
from file_manager import get_histogram_data, get_lowest_highest_turn_counts, get_num_of_simulations, get_winner_counts, get_lowest_highest_evolution

from pathlib import Path

from scipy.optimize import curve_fit


def analyse():
    num_sims = get_num_of_simulations(HISTOGRAM_FILE)
    hist = get_histogram_data(HISTOGRAM_FILE, NUM_BINS)
    wins_list = get_winner_counts(HISTOGRAM_FILE, NUM_PLAYERS)
    lowest_turns, highest_turns = get_lowest_highest_turn_counts(LOWEST_FILE, HIGHEST_FILE, MAX_TURNS)
    lowest_evol, highest_evol = get_lowest_highest_evolution(LOWEST_FILE, HIGHEST_FILE)
    
    min_max_turns_evolution_plot(lowest_evol, highest_evol)    
    win_count_analysis(wins_list, lowest_evol, highest_evol, num_sims)
    turn_count_plot(hist, lowest_turns, highest_turns, num_sims)
    
    """
    animate_histogram_evolution(
        hist,
        highest_turns,
        sims_per_frame=200_000_000,
        interval=30,
        save_file="histogram_evolution{VARIATION_TAG}.gif"
    )
    """
    
    

# -------------------
# Plotting functions
# -------------------
def exponential(x, A, k):
    return A * np.exp(-k * x)

def turn_count_plot(hist, lowest_turns, highest_turns, num_sims):
    """ Plot the distribution of turn counts for all games """

    mean_turns = np.average(np.arange(len(hist)), weights=hist)
    

    # Plot histogram
    plt.figure(figsize=(10, 5))
    plt.plot(hist, label=f"Min: {lowest_turns}, Max: {highest_turns}")
    
    
    plt.title("Distribution of Game Lengths")
    plt.xlabel("Number of Turns")
    plt.ylabel("Number of Games")
    plt.grid(True, linestyle="--", alpha=0.5)

    # Mean line
    plt.axvline(mean_turns, 
                color='red', 
                linestyle='--', 
                alpha=0.5, 
                label=f"Mean = {mean_turns:.0f}")

    # Peak line
    max_bin = hist.argmax()
    plt.axvline(max_bin, 
                color='orange', 
                linestyle='-.', 
                alpha=0.7, 
                label=f"Peak # turns = {max_bin:.0f}")
    
    
    # Only fit after the mean and up to y=10
    x = np.arange(len(hist))
    fit_ymin = 10
    tail_mask = (
        (x >= mean_turns) &
        (hist >= fit_ymin)
    )

    x_tail = x[tail_mask]
    y_tail = hist[tail_mask]

    params, _ = curve_fit(
        exponential,
        x_tail,
        y_tail,
        p0=[hist[int(mean_turns)], 0.01]
    )

    A, k = params

    x_fit = np.linspace(int(mean_turns), highest_turns, 500)
    y_fit = exponential(x_fit, A, k)
    
    plt.plot(x_fit, y_fit, 'k-', linewidth=1, label=f'Exp fit (k={k:.4f})')
    
    num_games_label = num_sims
    if num_sims >= 1_000_000:
        num_games_label = str(num_sims//1_000_000) + " million"
    if num_sims >= 1_000_000_000:
        num_games_label = f"{num_sims/1_000_000_000:.2f} billion"
    
    plt.plot([], [], ' ', label=f"{num_games_label} games")
    plt.legend()
    
    plt.yscale("log")
    ax = plt.gca()
    max_x_rounded_up = ((highest_turns + 999) // 1000) * 1000
    max_y_rounded_up = hist[max_bin] * 2
    ax.set_xlim([0, max_x_rounded_up])
    ax.set_ylim([0.8, max_y_rounded_up])
    
    
    plt.tight_layout()
    plt.savefig(Path(f"{PLOTS_FOLDER}/{VARIATION_TAG}_turn_count_plot.png"), dpi=300, bbox_inches="tight")
    plt.show()
    
    
    
def min_max_turns_evolution_plot(lowest_evol, highest_evol):
    """ Plotting shortest and longest found games against number of simulations """
    plt.figure(figsize=(10, 6))
    
    x = lowest_evol["num_sims"]
    y = lowest_evol["turns"]
    
    plt.plot(x, y)
    
    plt.title("Shortest found games against number of simulations")
    plt.xlabel("Number of Simulations")
    plt.ylabel("Number of Turns")
    plt.grid(True, linestyle="--", alpha=0.5)
    
    
    plt.xscale("log")
    
    plt.tight_layout()
    plt.savefig(Path(f"{PLOTS_FOLDER}/{VARIATION_TAG}_shortest_plot.png"), dpi=300, bbox_inches="tight")
    plt.show()
    
    
    # longest
    plt.figure(figsize=(10, 6))
    
    x = highest_evol["num_sims"]
    y = highest_evol["turns"]
    
    plt.plot(x, y)
        
    plt.title("Longest found games against number of simulations")
    plt.xlabel("Number of Simulations")
    plt.ylabel("Number of Turns")
    plt.grid(True, linestyle="--", alpha=0.5)
    
    
    plt.xscale("log")
    
    plt.tight_layout()
    plt.savefig(Path(f"{PLOTS_FOLDER}/{VARIATION_TAG}_longest_plot.png"), dpi=300, bbox_inches="tight")
    plt.show()
    
    
# ---------------------------------------
# Histogram evolution animation function
# ---------------------------------------

    
def animate_histogram_evolution(hist, 
                                highest_turns,
                                sims_per_frame=1000, 
                                interval=30, 
                                save_file=None, 
                                random_seed=None):
    """ Animate the evolution of a histogram """

    hist = np.asarray(hist, dtype=np.int64)

    num_bins = len(hist)
    total_sims = hist.sum()

    # Expand histogram into one array of events
    events = np.repeat(np.arange(num_bins), hist)

    rng = np.random.default_rng(random_seed)
    rng.shuffle(events)

    running_hist = np.zeros(num_bins, dtype=np.int64)

    fig, ax = plt.subplots(figsize=(12, 5))

    bars = ax.bar(np.arange(num_bins),
                  running_hist,
                  width=1.0,
                  align="center")

    max_bin = hist.argmax()
    max_x_rounded_up = ((highest_turns + 999) // 1000) * 1000
    max_y_rounded_up = hist[max_bin] * 3
    ax.set_xlim([0, max_x_rounded_up])
    ax.set_ylim([0.8, max_y_rounded_up])
    
    ax.set_yscale("symlog", linthresh=1)
    plt.grid(True, linestyle="--", alpha=0.5)

    ax.set_xlabel("Number of turns")
    ax.set_ylabel("Game count")

    title = ax.set_title("0 simulations")

    n_frames = (total_sims + sims_per_frame - 1) // sims_per_frame

    def update(frame):

        start = frame * sims_per_frame
        end = min(start + sims_per_frame, total_sims)

        new_events = events[start:end]

        additions = np.bincount(new_events, minlength=num_bins)
        running_hist[:] += additions

        changed = np.nonzero(additions)[0]

        for i in changed:
            bars[i].set_height(running_hist[i])

        title.set_text(f"{end:,} simulations")

        return [bars[i] for i in changed] + [title]

    ani = FuncAnimation(
        fig,
        update,
        frames=n_frames,
        interval=interval,
        blit=True,
        repeat=False,
    )

    if save_file is not None:
        ani.save(save_file, writer="pillow")
        #ani.save(save_file, dpi=150)

    plt.show()

    return ani



# ----------------------------
# Win rates analysis function
# ----------------------------


def win_count_analysis(wins_list, lowest_evol, highest_evol, num_sims):
    win_rates_list = wins_list/num_sims
    
    print("Win rates:\n" + 
          "\n".join(
              f"Player {i} - {rate:.2%}" 
              for i, rate in enumerate(win_rates_list)
        )
    )
    
    winners_shortest = lowest_evol["winner"]
    winners_longest = highest_evol["winner"]
    
    win_rates_shortest = (
        np.bincount(winners_shortest) / len(winners_shortest)
    ).tolist()
    
    win_rates_longest = (
        np.bincount(winners_longest) / len(winners_longest)
    ).tolist()
    
    print("\n Win rates shortest games:\n" + 
          "\n".join(
              f"Player {i} - {rate:.2%}" 
              for i, rate in enumerate(win_rates_shortest)
        )
    )
    
    
    print("\n Win rates longest games:\n" + 
          "\n".join(
              f"Player {i} - {rate:.2%}" 
              for i, rate in enumerate(win_rates_longest)
        )
    )
    