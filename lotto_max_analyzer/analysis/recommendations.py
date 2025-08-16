"""Number recommendation engine for Lotto Max."""

import logging
import random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from statistics import mean

from ..data.models import DrawResult, Recommendation
from ..config import (
    LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER, 
    HOT_NUMBER_THRESHOLD, COLD_NUMBER_THRESHOLD,
    NUMBER_RANGES
)
from .frequency import FrequencyAnalyzer
from .patterns import PatternAnalyzer


class RecommendationEngine:
    """Generates intelligent number recommendations based on historical analysis."""
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.logger = logging.getLogger(__name__)
        self.frequency_analyzer = FrequencyAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
    
    def generate_hot_number_picks(self, draws: List[DrawResult], count: int = 7) -> List[int]:
        """
        Generate number recommendations based on hot numbers (high frequency).
        
        Args:
            draws: List of DrawResult objects for analysis
            count: Number of recommendations to generate
            
        Returns:
            List of recommended numbers
        """
        if count != 7:
            raise ValueError("Must generate exactly 7 numbers for Lotto Max")
        
        self.logger.info(f"Generating hot number recommendations from {len(draws)} draws")
        
        # Get hot numbers from frequency analysis
        hot_numbers = self.frequency_analyzer.get_hot_numbers(draws)
        
        if len(hot_numbers) >= 7:
            # If we have enough hot numbers, select top 7
            recommendations = hot_numbers[:7]
        else:
            # If not enough hot numbers, supplement with highest frequency numbers
            frequency = self.frequency_analyzer.calculate_number_frequency(draws)
            sorted_by_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
            
            recommendations = hot_numbers[:]
            for num, _ in sorted_by_freq:
                if num not in recommendations and len(recommendations) < 7:
                    recommendations.append(num)
        
        # Ensure we have exactly 7 unique numbers
        recommendations = list(dict.fromkeys(recommendations))[:7]
        
        # If still not enough, fill with random high-frequency numbers
        if len(recommendations) < 7:
            frequency = self.frequency_analyzer.calculate_number_frequency(draws)
            available = [n for n in range(1, 51) if n not in recommendations]
            available.sort(key=lambda x: frequency.get(x, 0), reverse=True)
            recommendations.extend(available[:7-len(recommendations)])
        
        return sorted(recommendations)
    
    def generate_cold_number_picks(self, draws: List[DrawResult], count: int = 7) -> List[int]:
        """
        Generate number recommendations based on cold numbers (low frequency).
        
        Args:
            draws: List of DrawResult objects for analysis
            count: Number of recommendations to generate
            
        Returns:
            List of recommended numbers
        """
        if count != 7:
            raise ValueError("Must generate exactly 7 numbers for Lotto Max")
        
        self.logger.info(f"Generating cold number recommendations from {len(draws)} draws")
        
        # Get cold numbers and overdue numbers
        cold_numbers = self.frequency_analyzer.get_cold_numbers(draws)
        overdue_numbers = self.frequency_analyzer.get_overdue_numbers(draws, threshold_days=21)
        
        # Combine cold and overdue numbers (overdue numbers are just number, not tuples)
        overdue_nums = [num for num, _ in overdue_numbers]
        candidate_numbers = list(set(cold_numbers + overdue_nums))
        
        if len(candidate_numbers) >= 7:
            # Prioritize overdue numbers, then cold numbers
            recommendations = []
            
            # Add overdue numbers first
            for num in overdue_nums:
                if len(recommendations) < 7:
                    recommendations.append(num)
            
            # Fill with cold numbers
            for num in cold_numbers:
                if num not in recommendations and len(recommendations) < 7:
                    recommendations.append(num)
            
            recommendations = recommendations[:7]
        else:
            # If not enough cold/overdue numbers, use lowest frequency numbers
            frequency = self.frequency_analyzer.calculate_number_frequency(draws)
            sorted_by_freq = sorted(frequency.items(), key=lambda x: x[1])
            
            recommendations = candidate_numbers[:]
            for num, _ in sorted_by_freq:
                if num not in recommendations and len(recommendations) < 7:
                    recommendations.append(num)
        
        return sorted(recommendations[:7])
    
    def generate_balanced_picks(self, draws: List[DrawResult], count: int = 7) -> List[int]:
        """
        Generate balanced number recommendations combining multiple strategies.
        
        Args:
            draws: List of DrawResult objects for analysis
            count: Number of recommendations to generate
            
        Returns:
            List of recommended numbers
        """
        if count != 7:
            raise ValueError("Must generate exactly 7 numbers for Lotto Max")
        
        self.logger.info(f"Generating balanced recommendations from {len(draws)} draws")
        
        # Get various analysis results
        frequency = self.frequency_analyzer.calculate_number_frequency(draws)
        hot_numbers = self.frequency_analyzer.get_hot_numbers(draws)
        cold_numbers = self.frequency_analyzer.get_cold_numbers(draws)
        overdue_numbers = [num for num, _ in self.frequency_analyzer.get_overdue_numbers(draws, threshold_days=30)]
        
        # Get pattern insights
        pattern_summary = self.pattern_analyzer.get_pattern_summary(draws)
        odd_even_analysis = pattern_summary['odd_even_analysis']
        range_analysis = pattern_summary['range_analysis']
        
        # Strategy: Mix hot, medium, and strategic numbers
        recommendations = []
        
        # 1. Include 2-3 hot numbers (but not too many to avoid over-concentration)
        hot_count = min(3, len(hot_numbers))
        recommendations.extend(hot_numbers[:hot_count])
        
        # 2. Include 1-2 overdue numbers (contrarian approach)
        overdue_count = min(2, len(overdue_numbers))
        for num in overdue_numbers:
            if num not in recommendations and len(recommendations) < hot_count + overdue_count:
                recommendations.append(num)
        
        # 3. Ensure good odd/even balance based on historical patterns
        current_odd = sum(1 for n in recommendations if n % 2 == 1)
        current_even = len(recommendations) - current_odd
        
        # Target the most common odd/even pattern
        most_common_pattern = odd_even_analysis['most_common_pattern'][0]
        target_odd, target_even = map(int, most_common_pattern.split('-'))
        
        # 4. Fill remaining slots with balanced selection
        remaining_slots = 7 - len(recommendations)
        available_numbers = [n for n in range(1, 51) if n not in recommendations]
        
        # Separate available numbers by odd/even
        available_odd = [n for n in available_numbers if n % 2 == 1]
        available_even = [n for n in available_numbers if n % 2 == 0]
        
        # Calculate how many more odd/even numbers we need
        needed_odd = max(0, target_odd - current_odd)
        needed_even = max(0, target_even - current_even)
        
        # Adjust if we need more numbers than available slots
        if needed_odd + needed_even > remaining_slots:
            ratio = remaining_slots / (needed_odd + needed_even)
            needed_odd = int(needed_odd * ratio)
            needed_even = remaining_slots - needed_odd
        
        # 5. Ensure good range distribution
        range_counts = defaultdict(int)
        for num in recommendations:
            for range_name, (min_val, max_val) in NUMBER_RANGES.items():
                if min_val <= num <= max_val:
                    range_counts[range_name] += 1
                    break
        
        # Select remaining numbers with range balance in mind
        self._add_balanced_numbers(
            recommendations, available_odd, available_even,
            needed_odd, needed_even, remaining_slots,
            frequency, range_counts
        )
        
        # 6. Final validation and adjustment
        if len(recommendations) < 7:
            # Fill any remaining slots with medium-frequency numbers
            available = [n for n in range(1, 51) if n not in recommendations]
            available.sort(key=lambda x: abs(frequency.get(x, 0) - mean(frequency.values())))
            recommendations.extend(available[:7-len(recommendations)])
        
        return sorted(recommendations[:7])
    
    def create_full_combination(self, draws: List[DrawResult], strategy: str) -> List[int]:
        """
        Create a full 7-number combination using the specified strategy.
        
        Args:
            draws: List of DrawResult objects for analysis
            strategy: Strategy to use ('hot_numbers', 'cold_numbers', 'balanced')
            
        Returns:
            List of 7 recommended numbers
            
        Raises:
            ValueError: If strategy is invalid or insufficient data
        """
        valid_strategies = ['hot_numbers', 'cold_numbers', 'balanced']
        if strategy not in valid_strategies:
            raise ValueError(f"Strategy must be one of {valid_strategies}")
        
        if len(draws) < 50:
            raise ValueError("Need at least 50 draws for reliable recommendations")
        
        self.logger.info(f"Creating full combination using {strategy} strategy")
        
        if strategy == 'hot_numbers':
            numbers = self.generate_hot_number_picks(draws)
        elif strategy == 'cold_numbers':
            numbers = self.generate_cold_number_picks(draws)
        else:  # balanced
            numbers = self.generate_balanced_picks(draws)
        
        # Ensure exactly 7 unique numbers
        numbers = list(dict.fromkeys(numbers))[:7]
        
        if len(numbers) < 7:
            # This shouldn't happen with proper implementation, but safety check
            available = [n for n in range(1, 51) if n not in numbers]
            numbers.extend(random.sample(available, 7 - len(numbers)))
        
        return sorted(numbers)
    
    def generate_recommendation_with_rationale(self, draws: List[DrawResult], strategy: str) -> Recommendation:
        """
        Generate a complete recommendation with detailed rationale.
        
        Args:
            draws: List of DrawResult objects for analysis
            strategy: Strategy to use
            
        Returns:
            Recommendation object with numbers, confidence, and rationale
        """
        if strategy == 'mathematical':
            # Use mathematical randomizer
            from .mathematical_randomizer import MathematicalRandomizer
            randomizer = MathematicalRandomizer()
            return randomizer.generate_numbers(draws, 'mathematical')
        
        numbers = self.create_full_combination(draws, strategy)
        
        # Calculate confidence based on data quality and strategy
        confidence = self._calculate_confidence(draws, numbers, strategy)
        
        # Generate detailed rationale
        rationale = self._generate_rationale(draws, numbers, strategy)
        
        return Recommendation(
            strategy=strategy,
            numbers=numbers,
            confidence=confidence,
            rationale=rationale
        )
    
    def get_multiple_recommendations(self, draws: List[DrawResult], 
                                   strategies: Optional[List[str]] = None) -> Dict[str, Recommendation]:
        """
        Generate recommendations using multiple strategies.
        
        Args:
            draws: List of DrawResult objects for analysis
            strategies: List of strategies to use (default: all strategies)
            
        Returns:
            Dictionary mapping strategy names to Recommendation objects
        """
        if strategies is None:
            strategies = ['hot_numbers', 'cold_numbers', 'balanced', 'mathematical']
        
        recommendations = {}
        
        for strategy in strategies:
            try:
                if strategy == 'mathematical':
                    # Use mathematical randomizer
                    from .mathematical_randomizer import MathematicalRandomizer
                    randomizer = MathematicalRandomizer()
                    recommendation = randomizer.generate_numbers(draws, 'mathematical')
                else:
                    recommendation = self.generate_recommendation_with_rationale(draws, strategy)
                recommendations[strategy] = recommendation
                self.logger.info(f"Generated {strategy} recommendation: {recommendation.numbers}")
            except Exception as e:
                self.logger.error(f"Failed to generate {strategy} recommendation: {e}")
        
        return recommendations
    
    def _add_balanced_numbers(self, recommendations: List[int], available_odd: List[int], 
                            available_even: List[int], needed_odd: int, needed_even: int,
                            remaining_slots: int, frequency: Dict[int, int], 
                            range_counts: Dict[str, int]):
        """Add numbers to recommendations while maintaining balance."""
        # Sort available numbers by frequency (medium frequency preferred for balance)
        avg_freq = mean(frequency.values())
        
        available_odd.sort(key=lambda x: abs(frequency.get(x, 0) - avg_freq))
        available_even.sort(key=lambda x: abs(frequency.get(x, 0) - avg_freq))
        
        # Add needed odd numbers
        added_odd = 0
        for num in available_odd:
            if added_odd < needed_odd and len(recommendations) < 7:
                recommendations.append(num)
                added_odd += 1
        
        # Add needed even numbers
        added_even = 0
        for num in available_even:
            if added_even < needed_even and len(recommendations) < 7:
                recommendations.append(num)
                added_even += 1
        
        # Fill any remaining slots with best available numbers
        remaining = 7 - len(recommendations)
        if remaining > 0:
            all_available = [n for n in range(1, 51) if n not in recommendations]
            all_available.sort(key=lambda x: abs(frequency.get(x, 0) - avg_freq))
            recommendations.extend(all_available[:remaining])
    
    def _calculate_confidence(self, draws: List[DrawResult], numbers: List[int], strategy: str) -> float:
        """Calculate confidence score for the recommendation."""
        base_confidence = 0.7  # Base confidence
        
        # Adjust based on data quantity
        data_quality = min(1.0, len(draws) / 200)  # Optimal at 200+ draws
        
        # Adjust based on strategy
        strategy_confidence = {
            'hot_numbers': 0.8,    # High confidence in frequency patterns
            'cold_numbers': 0.6,   # Lower confidence in contrarian approach
            'balanced': 0.9        # Highest confidence in balanced approach
        }.get(strategy, 0.7)
        
        # Adjust based on number distribution quality
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        even_count = 7 - odd_count
        balance_score = 1.0 - abs(3.5 - odd_count) / 3.5  # Penalty for extreme imbalance
        
        # Calculate final confidence
        confidence = base_confidence * data_quality * strategy_confidence * balance_score
        
        return min(1.0, max(0.1, confidence))  # Clamp between 0.1 and 1.0
    
    def _generate_rationale(self, draws: List[DrawResult], numbers: List[int], strategy: str) -> str:
        """Generate detailed rationale for the recommendation."""
        frequency = self.frequency_analyzer.calculate_number_frequency(draws)
        
        rationale_parts = []
        
        # Strategy explanation
        if strategy == 'hot_numbers':
            rationale_parts.append(f"Hot number strategy based on {len(draws)} historical draws.")
            rationale_parts.append("Selected numbers with highest frequency of appearance.")
        elif strategy == 'cold_numbers':
            rationale_parts.append(f"Cold number strategy based on {len(draws)} historical draws.")
            rationale_parts.append("Selected numbers that are overdue or have low frequency.")
        else:  # balanced
            rationale_parts.append(f"Balanced strategy combining multiple factors from {len(draws)} draws.")
            rationale_parts.append("Mixed hot numbers, overdue numbers, and pattern-based selections.")
        
        # Number frequency analysis
        avg_freq = sum(frequency[n] for n in numbers) / len(numbers)
        total_avg = sum(frequency.values()) / len(frequency)
        
        if avg_freq > total_avg * 1.1:
            rationale_parts.append("Selected numbers appear more frequently than average.")
        elif avg_freq < total_avg * 0.9:
            rationale_parts.append("Selected numbers appear less frequently than average.")
        else:
            rationale_parts.append("Selected numbers have balanced frequency distribution.")
        
        # Odd/even analysis
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        rationale_parts.append(f"Odd/even split: {odd_count}-{7-odd_count} matches common patterns.")
        
        # Range analysis
        range_counts = defaultdict(int)
        for num in numbers:
            for range_name, (min_val, max_val) in NUMBER_RANGES.items():
                if min_val <= num <= max_val:
                    range_counts[range_name] += 1
                    break
        
        if len(range_counts) >= 4:
            rationale_parts.append("Numbers well-distributed across different ranges.")
        
        return " ".join(rationale_parts)