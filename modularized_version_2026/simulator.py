from collections import deque

def simulate_game(num_players, initial_hands, max_turns):
    """ Simulate a single game, returns summary """
    hands = [deque(h) for h in initial_hands]
    desk = []
    turn = 0
    player = 0
    active_players = num_players

    while turn < max_turns:
        # skip empty player
        if num_players >= 3 and not hands[player]:
            player = (player + 1) % num_players
            continue

        # win?
        if active_players <= 1:
            break

        # play a card
        card = hands[player].popleft()
        desk.append(card)

        # check match
        if card in desk[:-1]:
            matching_card = desk[-1]
            idx = desk.index(matching_card)
            gain = desk[idx:]
            del desk[idx:]
            hands[player].extend(gain)
        else:
            # check for empty hand at end of turn
            if not hands[player]:
                active_players -= 1
            player = (player + 1) % num_players

        turn += 1

    return {
        "initial_hands": initial_hands,
        "turns": turn,
        "winner": player
    }