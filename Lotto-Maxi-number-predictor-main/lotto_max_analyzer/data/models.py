"""Data models for Lotto Max Analyzer."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import re


@dataclass
class DrawResult:
    """Represents a single Lotto Max draw result."""
    date: datetime
    numbers: List[int]  # 7 winning numbers
    bonus: int          # Bonus number
    jackpot_amount: float
    draw_id: str

    def __post_init__(self):
        """Validate the draw result data."""
        # Validate numbers list
        if len(self.numbers) != 7:
            raise ValueError(f"Expected 7 numbers, got {len(self.numbers)}")
        
        # Validate number ranges (1-50 for Lotto Max)
        for num in self.numbers:
            if not isinstance(num, int) or num < 1 or num > 50:
                raise ValueError(f"Invalid number {num}. Numbers must be integers between 1 and 50")
        
        # Check for duplicates
        if len(set(self.numbers)) != 7:
            raise ValueError("Numbers must be unique")
        
        # Validate bonus number
        if not isinstance(self.bonus, int) or self.bonus < 1 or self.bonus > 50:
            raise ValueError(f"Invalid bonus number {self.bonus}. Must be integer between 1 and 50")
        
        # Validate jackpot amount
        if self.jackpot_amount < 0:
            raise ValueError("Jackpot amount cannot be negative")
        
        # Validate draw_id format
        if not self.draw_id or not isinstance(self.draw_id, str):
            raise ValueError("Draw ID must be a non-empty string")
        
        # Sort numbers for consistency
        self.numbers = sorted(self.numbers)


@dataclass
class Pattern:
    """Represents a detected pattern in lottery draws."""
    type: str  # 'consecutive', 'odd_even', 'range'
    description: str
    frequency: int
    significance: float
    examples: List[List[int]]

    def __post_init__(self):
        """Validate pattern data."""
        valid_types = ['consecutive', 'odd_even', 'range']
        if self.type not in valid_types:
            raise ValueError(f"Pattern type must be one of {valid_types}")
        
        if self.frequency < 0:
            raise ValueError("Frequency cannot be negative")
        
        if not 0 <= self.significance <= 1:
            raise ValueError("Significance must be between 0 and 1")


@dataclass
class FrequencyStats:
    """Statistics for a specific number's frequency."""
    number: int
    count: int
    percentage: float
    last_seen: Optional[datetime]
    average_gap: float

    def __post_init__(self):
        """Validate frequency stats."""
        if not 1 <= self.number <= 50:
            raise ValueError("Number must be between 1 and 50")
        
        if self.count < 0:
            raise ValueError("Count cannot be negative")
        
        if not 0 <= self.percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        
        if self.average_gap < 0:
            raise ValueError("Average gap cannot be negative")


@dataclass
class Recommendation:
    """Number recommendation with strategy and rationale."""
    strategy: str
    numbers: List[int]
    confidence: float
    rationale: str

    def __post_init__(self):
        """Validate recommendation data."""
        valid_strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        if self.strategy not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        
        if len(self.numbers) != 7:
            raise ValueError("Recommendation must contain exactly 7 numbers")
        
        # Validate number ranges
        for num in self.numbers:
            if not isinstance(num, int) or num < 1 or num > 50:
                raise ValueError(f"Invalid number {num}. Numbers must be integers between 1 and 50")
        
        # Check for duplicates
        if len(set(self.numbers)) != 7:
            raise ValueError("Recommended numbers must be unique")
        
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        
        if not self.rationale:
            raise ValueError("Rationale cannot be empty")
        
        # Sort numbers for consistency
        self.numbers = sorted(self.numbers)