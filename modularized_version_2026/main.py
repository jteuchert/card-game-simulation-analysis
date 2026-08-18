from config import NUM_PLAYERS, NUM_SIMULATIONS, MAX_TURNS, NUM_BINS, FULL_DECK, HISTOGRAM_FILE, HIGHEST_FILE, LOWEST_FILE, SIMS_PER_WORKER
from hands_generator import generate_hands
from simulator import simulate_game
from data_manager import DataManager
from file_manager import prepare_lowest_highest_files, prepare_hist_file, save_histogram_data, save_new_lowest_highest, get_histogram_data, get_num_of_simulations, get_winner_counts, get_lowest_highest_turn_counts
from analysis import analyse

import time

import os
from concurrent.futures import ProcessPoolExecutor

#import cProfile
#import pstats

def worker(num_games):
    """ Worker process. Runs simulations and returns summary data. """
    
    manager = DataManager(num_bins=NUM_BINS, max_turns=MAX_TURNS, num_players=NUM_PLAYERS)

    for _ in range(num_games):
        initial_hands = generate_hands(FULL_DECK, NUM_PLAYERS)
        result = simulate_game(NUM_PLAYERS, initial_hands, MAX_TURNS)
        manager.add_result(result)

    return manager.get_all_results()

def merge_results(results):
    """ Combine worker outputs. """

    total_hist = get_histogram_data(HISTOGRAM_FILE, NUM_BINS)
    total_sims = get_num_of_simulations(HISTOGRAM_FILE)
    total_wins = get_winner_counts(HISTOGRAM_FILE, NUM_PLAYERS)

    lowest, highest = get_lowest_highest_turn_counts(LOWEST_FILE, HIGHEST_FILE, MAX_TURNS)

    lowest_history = []
    highest_history = []


    for result in results:
        total_wins = [sum(x) for x in zip(total_wins, result["wins"])]

        # merge histogram
        for i, value in enumerate(result["hist"]):
            total_hist[i] += value
            
            
        for item in result["lowest_history"]:
            if item[2] <= lowest:
                lowest_history.append([item[0] + total_sims, item[1], item[2], item[3]]) # item indices: 0 - num_finished_sims, 1 - hands list, 2 - lowest turn count, 3 - winner id
                
        for item in result["highest_history"]:
            if item[2] >= highest:
                highest_history.append([item[0] + total_sims, item[1], item[2], item[3]])
                
        total_sims += sum(result["wins"])


    return {
        "num_sims": total_sims,
        "wins": total_wins,
        "hist": total_hist,
        "lowest": lowest_history,
        "highest": highest_history
    }


def run_batch(workers):
    # Start multiprocessing
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(worker, [SIMS_PER_WORKER] * workers))


    # Combine worker results
    final = merge_results(results)


    # Save final data
    save_histogram_data(
        final["num_sims"],
        HISTOGRAM_FILE,
        final["hist"],
        final["wins"]
    )
    
    
    final_lowest = MAX_TURNS
    final_highest = 0
    
    if final["lowest"]:
        for i in final["lowest"]:
            if i[2] <= final_lowest:
                final_lowest = i[2]
                save_new_lowest_highest(
                    LOWEST_FILE,
                    i[0],
                    i[1],
                    i[2],
                    i[3]
                )

    # i indices: 0 - num_finished_sims, 1 - hands list, 2 - lowest turn count, 3 - winner id
    
    if final["highest"]:
        for i in final["highest"]:
            if i[2] >= final_highest:
                final_highest = i[2]
                save_new_lowest_highest(
                    HIGHEST_FILE,
                    i[0],
                    i[1],
                    i[2],
                    i[3]
                )

def main():
    # Prepare output files
    prepare_hist_file(HISTOGRAM_FILE, NUM_BINS, NUM_PLAYERS)
    prepare_lowest_highest_files(NUM_PLAYERS, LOWEST_FILE, HIGHEST_FILE)


    # Determine workers
    workers = max(1, os.cpu_count() - 1)
    batch_size = workers*SIMS_PER_WORKER
    
    num_batches = NUM_SIMULATIONS//batch_size
    left = NUM_SIMULATIONS - num_batches*batch_size
    

    # Run simulations    
    print(f"Starting to run {NUM_SIMULATIONS:,} simulations in total.")
    print(f"Progress: {0:.0%} [{0} / {NUM_SIMULATIONS:,}] \n")
    for i in range(num_batches):
        print(f"Running {SIMS_PER_WORKER*workers:,} simulations " f"using {workers} workers")
        run_batch(workers)
        print(f"Progress: {((i+1)*batch_size)/NUM_SIMULATIONS:.0%} [{(i+1)*batch_size:,} / {NUM_SIMULATIONS:,}] \n")
    
    last_workers = left//SIMS_PER_WORKER
    print(f"Running {SIMS_PER_WORKER*last_workers:,} simulations " f"using {last_workers} workers")
    if last_workers > 0:
        run_batch(last_workers)

    num_actual_sims = SIMS_PER_WORKER * (workers*num_batches + last_workers)
    print(f"Progress: {num_actual_sims/NUM_SIMULATIONS:.0%} [{num_actual_sims:,} / {NUM_SIMULATIONS:,}] \n")

    return num_actual_sims

if __name__ == "__main__":
    #profiler = cProfile.Profile()
    #profiler.enable()
    start_time = time.time()
    num_actual_sims = main()
    end_time = time.time()
    duration = end_time - start_time
    
    duration_str = f"{duration:.2f} sec"
    if duration > 60:
        duration_str = f"{int(duration//60)} min {int(duration%60)} sec"
    
    print(f"Simulated {num_actual_sims:,} games in {duration_str} ({1000*duration/num_actual_sims:.2f}ms/game, {num_actual_sims/duration:.1f} games/s).")
    
    analyse()
    #profiler.disable()
    #stats = pstats.Stats(profiler)
    #stats.sort_stats("cumtime")
    #stats.print_stats(30)