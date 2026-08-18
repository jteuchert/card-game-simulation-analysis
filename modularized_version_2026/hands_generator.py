import random

def generate_hands(full_deck, num_players):
    """ Generate and return random hands for num_players """
    deck = full_deck.copy()
    random.shuffle(deck)
    hands = [[] for _ in range(num_players)]
    for j, card in enumerate(deck):
        hands[j % num_players].append(card)
    return hands