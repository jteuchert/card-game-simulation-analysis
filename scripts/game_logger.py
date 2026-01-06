""" Script for generating log files given the initial hands.
Usage:
    - Define initial hands (values 2-10, J, Q, K, A max 4 each, max 2 Jokers) or read from summary file
    - Define output file name LOG_FILE below
    - Run script
"""

import random
import pandas as pd
from pathlib import Path
from collections import Counter
import json


""" Config """
# Short demo game:
demo_init = [["2", "3", "8"], 
             ["8", "A", "J"]
             ]

# Longer demo game:
demo_long_init = [["3", "9", "8", "J", "6", "4", "9", "2", "5", "Q", "K", "A", "3", "Q", "K", "3", "6", "7", "7", "4", "8", "A", "Q", "K", "A", "5", "8"], 
                ["A", "J", "5", "7", "J", "8", "10", "4", "9", "3", "5", "2", "Joker", "Q", "9", "K", "10", "7", "4", "2", "10", "Joker", "6", "J", "6", "2", "10"]
                ]

# Shortest game:
shortest_init = [["2", "4", "6", "8", "10", "Q", "A", "2", "5", "7", "9", "J", "K", "Joker", "2", "5", "7", "9", "J", "K", "Joker", "6", "8", "10", "Q", "K", "A"], 
                ["3", "5", "7", "9", "J", "K", "2", "3", "4", "6", "8", "10", "Q", "A", "3", "4", "3", "6", "8", "10", "Q", "A", "4", "5", "7", "9", "J"]
                ]


def read_hands(file_name, game_idx):
    df = pd.read_csv(file_name)
    init = []
    for col in df.filter(like="hand_").columns:
        df[col] = df[col].apply(json.loads)
        init.append(df.iloc[game_idx][col])
    return init

"""" Set initial hands here! """
# change here to another preset, define manually or read from summary file
initial_hands = demo_init
#initial_hands = read_hands("summary_batch_0_2p.csv", 0)


NUM_PLAYERS = len(initial_hands)
LOG_FOLDER = Path("game_logs")
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path("game_logs/log_demo_4p.csv") # output log file name

MAX_TURNS = 10000


""" Suits """
def assign_random_suits(values, suits=("H", "D", "C", "S")):
    # Count how many of each value are requested
    counts = Counter(values)

    # Warn if too many non-joker cards
    for value, count in counts.items():
        if value != "Joker" and count > len(suits):
            print(f"Warning: {count} '{value}' cards requested")

    # Warn if too many jokers
    if counts.get("Joker", 0) > 2:
        print(f"Warning: {counts['Joker']} Jokers requested (max 2)")

    # Build available cards for normal values
    available = {
        value: random.sample(
            [f"{value}{s}" for s in suits],
            min(counts[value], len(suits))
        )
        for value in counts if value != "Joker"
    }
    
    # Build available jokers
    joker_available = random.sample(
        ["Joker1", "Joker2"],
        min(counts.get("Joker", 0), 2)
    )

    result = []

    # Assign cards in the original order
    for value in values:
        if value == "Joker":
            if joker_available:
                result.append(joker_available.pop())
            else:
                result.append(None) 
        else:
            if available[value]:
                result.append(available[value].pop())
            else:
                result.append(None)
    return result


""" Core simulation """
def simulate_game():
    
    #### Updated suiting block: Combines hands to a list, applies suiting and separates into hands again
    input_list = []
    hands = []
    hand_sizes = []
    for p in range(NUM_PLAYERS):
        hand_sizes.append(len(initial_hands[p]))
        input_list += initial_hands[p].copy() 
    suited_list = assign_random_suits(input_list)
    progressor = 0
    for p in range(NUM_PLAYERS):
        hands.append(suited_list[progressor:progressor + hand_sizes[p]])
        progressor += hand_sizes[p]  
    ####
    
    desk = []
    turn = 0
    player = 0
    
    # Create log file
    if not LOG_FILE.exists():
        hand_cols = [f"hand_{p}" for p in range(NUM_PLAYERS)]
        cols = ["turn", "player_turn", "desk"] + hand_cols
        pd.DataFrame(columns=cols).to_csv(LOG_FILE, index=False)

    while turn < MAX_TURNS:
        # skip empty player
        if NUM_PLAYERS >= 3 and not hands[player]:
            player = (player + 1) % NUM_PLAYERS
            continue

        # log
        #print(desk)
        row = {
            "turn": turn,
            "player_turn": player,
            "desk": json.dumps(desk) #.tolist()
        }
        for p in range(NUM_PLAYERS):
            key = f"hand_{p}"
            row[key] = json.dumps(hands[p])
        df = pd.DataFrame([row])
        df.to_csv(LOG_FILE, mode="a", header=False, index=False)


        # win?
        if sum(1 for h in hands if len(h) == 0) > NUM_PLAYERS - 2:
            break

        # play a card
        card = hands[player].pop(0)
        desk.append(card)

        # check match
        desk_values = desk.copy()
        
        # Get card values (4C --> 4, Joker1 --> Joker etc.)
        for i in range(len(desk_values)):
            if desk_values[i] == "Joker1" or desk_values[i] == "Joker2":
                desk_values[i] = "Joker"
            else:
                desk_values[i] = desk_values[i][:-1]
        
        
        if len(desk_values) != len(set(desk_values)):
            # Add extra row (no additional turn!) for animation
            row = {
                "turn": turn,
                "player_turn": player,
                "desk": json.dumps(desk), #.tolist()
            }
            for p in range(NUM_PLAYERS):
                key = f"hand_{p}"
                row[key] = json.dumps(hands[p])
            df = pd.DataFrame([row])
            df.to_csv(LOG_FILE, mode="a", header=False, index=False)
            
        
            matching_card_value = desk_values[-1] # get value of last card
            idx = desk_values.index(matching_card_value) # find first occurence of that value
            gain = desk[idx:]
            del desk[idx:]
            hands[player].extend(gain)
            
                 
        else:
            player = (player + 1) % NUM_PLAYERS

        turn += 1
    
    return


if __name__ == "__main__":
    simulate_game()
    print("Done.")