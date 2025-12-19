""" 
Script for automatic rendering of game animations using manim.

Usage:
    - Make sure the folder "cards" (found in "data"), containing the card images, is in the same folder as this script. 
    - Create log file with game_logger.py
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

CARD_SCALE = 0.4
CARD_OVERLAP = 0.3 # lower --> more overlap
ROW_Y = [0, 2.5, -2.5] # desk, hand_A, hand_B
ROW_X_OFFSET = -6
LABEL_X = -6.7
LABEL_Y_OFFSET = 1.25
row_labels = ["Desk:", "Player A:", "Player B:"]

LOG_FILE = Path("game_logs/log_shortest.csv")


# Read states from log file
log = pd.read_csv(LOG_FILE)
log["hand_0"] = log["hand_0"].apply(json.loads)
log["hand_1"] = log["hand_1"].apply(json.loads)
log["desk"] = log["desk"].apply(json.loads)


# ---------------------------------------------------
# Highlight functions
# ---------------------------------------------------
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


# ---------------------------------------------------
# Hands/desk list reading
# ---------------------------------------------------
# Get game state at given turn from log
def get_state(turn):  
    hand_A = log.iloc[turn]["hand_0"]
    hand_B = log.iloc[turn]["hand_1"]
    desk = log.iloc[turn]["desk"]
    
    return [desk, hand_A, hand_B]



# ---------------------------------------------------
# Core classes
# ---------------------------------------------------
# Card class
class Card(ImageMobject):
    def __init__(self, name):
        super().__init__(f"cards/{name}.png")
        self.name = name
        self.scale(CARD_SCALE)

# Main loop
class CardGame(Scene):
    def construct(self):
        states = [get_state(turn) for turn in range(len(log.index))]

        self.cards = {}
        self.rows = [Group(), Group(), Group()]
        self.add(*self.rows)

        self.init_state(states[0])
        
        # Add labels
        self.labels = []

        for i, label in enumerate(row_labels):
            t = Text(label, font_size=20)
            anchor = Dot(point=[LABEL_X, ROW_Y[i] + LABEL_Y_OFFSET, 0], radius=0)
            t.next_to(anchor, RIGHT, buff=0.1)
            self.labels.append(t)

        self.add(*self.labels)
        
        
        for a, b in zip(states, states[1:]):
            self.transition(a, b)
            self.wait(0.5)

    # --------------------
    # Initialization
    # --------------------
    def init_state(self, state):
        for r, row in enumerate(state):
            for card_name in row:
                card = Card(card_name)
                self.cards[card_name] = card
                self.rows[r].add(card)

        self.layout(animate=False)

    # --------------------
    # Layout
    # --------------------
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
            self.play(*anims, run_time=0.6)
            
           
    # --------------------
    # Highlight
    # --------------------
    # Short highlight animation of matching cards
    def highlight_cards(self, cards, color=YELLOW):
        highlights = [
            SurroundingRectangle(card, color=color, buff=0.05)
            for card in cards
        ]

        self.play(*[Create(h) for h in highlights], run_time=0.5)
        self.play(*[FadeOut(h) for h in highlights], run_time=0.5)

    # --------------------
    # Transition
    # --------------------
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

    # --------------------
    # Helpers
    # --------------------
    def positions(self, state):
        return {
            card: (r, i)
            for r, row in enumerate(state)
            for i, card in enumerate(row)
        }
