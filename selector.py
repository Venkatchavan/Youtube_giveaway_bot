"""
Random selection logic for picking giveaway winners.
"""
import random
from typing import List, Dict
from datetime import datetime
from models import Winner


class WinnerSelector:
    """Handles the random selection of winners from eligible participants."""
    
    def __init__(self, seed: int = None):
        """Initialize the selector with an optional random seed for reproducibility."""
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def pick_winners(self, eligible_usernames: List[str], num_winners: int, 
                    weighted_by_messages: bool = False, 
                    message_counts: Dict[str, int] = None) -> List[Winner]:
        """
        Pick random winners from eligible participants.
        
        Args:
            eligible_usernames: List of usernames eligible to win
            num_winners: Number of winners to select
            weighted_by_messages: If True, weight selection by message count
            message_counts: Dict mapping username to message count (required if weighted)
            
        Returns:
            List of Winner objects in draw order
            
        Raises:
            ValueError: If num_winners exceeds eligible participants
        """
        if num_winners > len(eligible_usernames):
            raise ValueError(
                f"Cannot select {num_winners} winners from {len(eligible_usernames)} eligible participants"
            )
        
        if num_winners <= 0:
            return []
        
        if weighted_by_messages and message_counts:
            selected_usernames = self._weighted_selection(
                eligible_usernames, num_winners, message_counts
            )
        else:
            # Simple random selection without replacement
            selected_usernames = random.sample(eligible_usernames, num_winners)
        
        # Create Winner objects with draw order
        winners = []
        for i, username in enumerate(selected_usernames, 1):
            winners.append(Winner(
                username=username,
                draw_order=i,
                timestamp=datetime.now()
            ))
        
        return winners
    
    def _weighted_selection(self, usernames: List[str], num_winners: int, 
                          message_counts: Dict[str, int]) -> List[str]:
        """
        Perform weighted random selection based on message counts.
        
        Args:
            usernames: List of eligible usernames
            num_winners: Number of winners to select
            message_counts: Dict mapping username to message count
            
        Returns:
            List of selected usernames
        """
        # Create weights list corresponding to usernames
        weights = [message_counts.get(username, 1) for username in usernames]
        
        # Use random.choices for weighted selection without replacement
        selected = []
        remaining_usernames = usernames.copy()
        remaining_weights = weights.copy()
        
        for _ in range(num_winners):
            if not remaining_usernames:
                break
                
            # Weighted random choice
            chosen_username = random.choices(
                remaining_usernames, 
                weights=remaining_weights, 
                k=1
            )[0]
            
            # Add to selected and remove from remaining
            selected.append(chosen_username)
            idx = remaining_usernames.index(chosen_username)
            remaining_usernames.pop(idx)
            remaining_weights.pop(idx)
        
        return selected
    
    def get_seed(self) -> int:
        """Get the current random seed for reproducibility."""
        return self.seed
    
    def set_seed(self, seed: int) -> None:
        """Set a new random seed."""
        self.seed = seed
        random.seed(seed)
