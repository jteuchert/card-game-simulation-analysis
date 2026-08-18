import numpy as np

class DataManager:
    def __init__(self, num_bins, max_turns, num_players):
        self.max_turns = max_turns
        self.lowest = max_turns
        self.highest = 0
        self.lowest_history = []
        self.highest_history = []
        self.num_finished_sims = 0
        self.hist = np.zeros(num_bins, dtype=np.uint64)
        self.wins = np.zeros(num_players, dtype=np.uint64)
    
    
    def add_result(self, result):
        self.num_finished_sims += 1
        bin_idx = min(result['turns'], self.max_turns)
        self.hist[bin_idx] += 1
        self.wins[result['winner']] += 1
        
        # Potentially save new lowest/highest found turn counts
        if result['turns'] <= self.lowest:
            # Save turn count and initial hands to lowest file
            self.lowest = result['turns']
            self.lowest_history.append([self.num_finished_sims, 
                                        result['initial_hands'], 
                                        self.lowest, 
                                        result['winner']])
            
        if result['turns'] >= self.highest:
            # Save turn count and initial hands to highest file
            self.highest = result['turns']
            self.highest_history.append([self.num_finished_sims, 
                                         result['initial_hands'],  
                                         self.highest, 
                                         result['winner']])
            
        
    def get_hist_results(self):
        return self.hist
    
    def get_wins_results(self):
        return self.wins
    
    def get_lowest_highest_results(self):
        return self.lowest_history, self.highest_history
    
    def get_all_results(self):
        return {"hist": self.hist, 
                "wins": self.wins, 
                "lowest_history": self.lowest_history, 
                "highest_history": self.highest_history
        }
