""" 
Script for automatic rendering of game animations using manim.

Usage:
    - Make sure the folder "cards" (found in "data"), containing the card images, is in the same folder as this script. 
    - Create log file with game_logger.py
    - Be aware that games with > 100 turns can take a long time to animate
    - Define LOG_FILE below to access that log
    - With manim installed (I reccommend to do it in a new environment since it works best with Python 3.10 or 3.11), run command:
        manim -pql game_animator.py CardGame 
        
    or for high quality:
        manim -pqh game_animator.py CardGame 
"""

from manim import *
from pathlib import Path
import json
import pandas as pd
from collections import defaultdict


LOG_FILE = Path("game_logs/log_demo.csv")
log = pd.read_csv(LOG_FILE)
log["desk"] = log["desk"].apply(json.loads)
NUM_PLAYERS = 0 # no need to set, will automatically be determined from the log file
for col in log.filter(like="hand_").columns:
    log[col] = log[col].apply(json.loads)
    NUM_PLAYERS += 1
    
    
CARD_SCALE = 0.4
CARD_OVERLAP = 0.3 # lower --> more overlap
ROW_X_OFFSET = -6
ROW_GAP = 0.4
LABEL_X = -6.7
row_labels = ["Desk:"] + [f"Player {i}:" for i in range(NUM_PLAYERS)]


# Card class
class Card(ImageMobject):
    def __init__(self, name):
        super().__init__(f"cards/{name}.png")
        self.name = name
        self.scale(CARD_SCALE)


""" Vertical card rows layout """
num_rows = NUM_PLAYERS + 1

# Measure card height
test_card = Card("2H")
card_height = test_card.height

required_height = num_rows * card_height + (num_rows-1) * ROW_GAP + num_rows*0.25 # extra space for label "Desk"
available_height = config.frame_height * 0.9  # leave margins

# Scale cards down if needed
if required_height > available_height:
    scale_factor = available_height / required_height
    CARD_SCALE *= scale_factor

# Recompute card height after scaling
test_card = Card("AS")
card_height = test_card.height

# Final row positions
start_y = (card_height / 2)
total_height = num_rows * card_height + (num_rows - 1) * ROW_GAP

ROW_Y = [
    total_height / 2 - (card_height / 2) - i * (card_height + ROW_GAP)
    for i in range(num_rows)
]

LABEL_Y_OFFSET = card_height/2 + 0.2


# Get numeric value (or "J", "Q", "K", "A") for a card
def card_value(name):
    if name == "Joker1" or name == "Joker2":
        return "Joker"
    return name[:-1]

# Get indices of matching cards
def matching_indices(card_names):
    groups = defaultdict(list)
    for i, name in enumerate(card_names):
        groups[card_value(name)].append(i)

    return [idxs for idxs in groups.values() if len(idxs) >= 2]


""" Desk/hands list reading """
# Get game state at given turn from log
def get_state(turn):      
    desk = log.iloc[turn]["desk"]
    curr_player = log.iloc[turn]["player_turn"]
    hands_list = []
    for col in log.filter(like="hand_").columns:
        hands_list.append(log.iloc[turn][col])
    
    state = [desk] + [lst for lst in hands_list]
    return [state, curr_player]



""" Main loop class """
class CardGame(Scene):
    def construct(self):
        states = [get_state(turn) for turn in range(len(log.index))] # a state looks like this: [[desk, hands], player_turn]

        self.cards = {}
        self.rows = [Group() for _ in range(NUM_PLAYERS + 1)]
        self.add(*self.rows)

        self.init_state(states[0])
        
        # Add labels
        self.labels = []
        
        for i, label in enumerate(row_labels):
            t = Text(label, color=WHITE, font_size=20)
            anchor = Dot(point=[LABEL_X, ROW_Y[i] + LABEL_Y_OFFSET, 0], radius=0)
            t.next_to(anchor, RIGHT, buff=0.1)
            self.labels.append(t)

        self.add(*self.labels)
        self.bring_to_back(*self.labels)
        

        for a, b in zip(states, states[1:]):
            curr_turn = a[1]
            # All idices of rows, escept for current player
            indices = [p+1 for p in range(NUM_PLAYERS) if p != curr_turn]
            # Highlight current player
            self.play(
                *[
                    self.labels[i].animate.set_color(WHITE)
                    for i in indices
                ] + [self.labels[curr_turn + 1].animate.set_color(RED)], # +1 offset for desk
                run_time=0.3
                )

            self.transition(a[0], b[0]) # index 0 to select card lists, not player_turn
            self.wait(0.5)

    """ Initialization """
    def init_state(self, state):
        for r, row in enumerate(state[0]): # index 0 to select card lists, not player_turn
            for card_name in row:
                card = Card(card_name)
                self.cards[card_name] = card
                self.rows[r].add(card)

        self.layout(animate=False)

    """" Layout """
    def layout(self, animate=True):
        anims = []
        for r, row in enumerate(self.rows):
            for i, card in enumerate(row):
                target = RIGHT * (i * CARD_OVERLAP) + UP * ROW_Y[r] + RIGHT * ROW_X_OFFSET
                if animate:
                    anims.append(card.animate.move_to(target))
                else:
                    card.move_to(target)

        if anims:
            self.play(*anims, run_time=0.5) #0.6
            
           
    """ Matching cards highlight """
    # Short highlight animation of matching cards
    def highlight_cards(self, cards, color=YELLOW):
        highlights = [
            SurroundingRectangle(card, color=color, buff=0.05)
            for card in cards
        ]

        self.play(*[Create(h) for h in highlights], run_time=0.4)
        self.play(*[FadeOut(h) for h in highlights], run_time=0.4)

    """ State transition """
    def transition(self, prev, nxt):
        prev_pos = self.positions(prev)
        next_pos = self.positions(nxt)

        moving = {c for c in prev_pos if prev_pos[c] != next_pos[c]}

        # Remove moving cards from all rows
        for row in self.rows:
            for card in list(row):
                if card.name in moving:
                    row.remove(card)

        # Rebuild each row in correct order
        for r, row in enumerate(nxt):
            target = self.rows[r]
            ordered_cards = [self.cards[name] for name in row]
            target.submobjects = ordered_cards.copy() 

        self.layout(animate=True)

        # Highlight desk matches
        desk_names = nxt[0] # 0 = index of desk row
        matches = matching_indices(desk_names)

        for idxs in matches:
            cards_to_highlight = [self.rows[0][i] for i in idxs] # 0 = index of desk row
            self.highlight_cards(cards_to_highlight)

    """ Helper """
    def positions(self, state):
        return {
            card: (r, i)
            for r, row in enumerate(state)
            for i, card in enumerate(row)
        }
