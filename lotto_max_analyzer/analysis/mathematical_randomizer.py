"""
Mathematical Randomizer for Lotto Max Analyzer.
Uses sophisticated algorithms and mathematical principles to generate lottery numbers.
"""

import numpy as np
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

from ..data.models import DrawResult, Recommendation
from .ml_predictor import MLPredictor


@dataclass
class RandomizerConfig:
    """Configuration for the mathematical randomizer."""
    use_fibonacci: bool = True
    use_prime_weights: bool = True
    use_golden_ratio: bool = True
    use_chaos_theory: bool = True
    use_statistical_bias: bool = True
    entropy_sources: List[str] = None
    
    def __post_init__(self):
        if self.entropy_sources is None:
            self.entropy_sources = ['time', 'system', 'mathematical']


class MathematicalRandomizer:
    """
    Advanced mathematical randomizer using multiple algorithms and entropy sources.
    
    This randomizer combines several mathematical principles:
    1. Fibonacci sequences for natural distribution
    2. Prime number theory for uniqueness
    3. Golden ratio for aesthetic balance
    4. Chaos theory for unpredictability
    5. Statistical bias correction
    6. Multiple entropy sources
    """
    
    def __init__(self, config: Optional[RandomizerConfig] = None):
        """Initialize the mathematical randomizer."""
        self.config = config or RandomizerConfig()
        self.logger = logging.getLogger(__name__)
        self.ml_predictor = MLPredictor()
        
        # Pre-calculate mathematical constants
        self.golden_ratio = (1 + np.sqrt(5)) / 2
        self.euler_number = np.e
        self.pi = np.pi
        
        # Pre-calculate prime numbers up to 50
        self.primes = self._generate_primes(50)
        
        # Pre-calculate Fibonacci sequence
        self.fibonacci = self._generate_fibonacci(50)
        
        # Initialize entropy pool
        self.entropy_pool = self._initialize_entropy_pool()
        
        self.logger.info("Mathematical randomizer initialized with advanced algorithms")

    def train_ml_model(self, historical_draws: List[DrawResult]):
        """Train the machine learning model."""
        self.logger.info("Starting ML model training...")
        self.ml_predictor.train(historical_draws)
        self.logger.info("ML model training complete.")
    
    def generate_numbers(self, historical_draws: List[DrawResult], 
                        strategy: str = 'mathematical') -> Recommendation:
        """
        Generate lottery numbers using mathematical algorithms.
        
        Args:
            historical_draws: Historical draw data for bias correction
            strategy: Generation strategy ('mathematical', 'chaos', 'fibonacci', 'prime', 'ml_hybrid')
            
        Returns:
            Recommendation with mathematically generated numbers
        """
        self.logger.info(f"Generating numbers using {strategy} strategy")
        
        if strategy == 'mathematical':
            numbers = self._generate_mathematical_numbers(historical_draws)
            reasoning = "Advanced mathematical algorithm combining multiple entropy sources"
        elif strategy == 'chaos':
            numbers = self._generate_chaos_numbers(historical_draws)
            reasoning = "Chaos theory-based generation with butterfly effect principles"
        elif strategy == 'fibonacci':
            numbers = self._generate_fibonacci_numbers(historical_draws)
            reasoning = "Fibonacci sequence-based generation following natural patterns"
        elif strategy == 'prime':
            numbers = self._generate_prime_numbers(historical_draws)
            reasoning = "Prime number theory-based generation for uniqueness"
        elif strategy == 'ml_hybrid':
            numbers = self._generate_ml_hybrid_numbers(historical_draws)
            reasoning = "Hybrid generation using a weighted scoring system of historical data and ML predictions"
        else:
            numbers = self._generate_mathematical_numbers(historical_draws)
            reasoning = "Default mathematical algorithm"
        
        # Calculate confidence based on mathematical properties
        confidence = self._calculate_mathematical_confidence(numbers, historical_draws)
        
        return Recommendation(
            numbers=sorted(numbers),
            strategy=f'mathematical_{strategy}',
            confidence=confidence,
            rationale=reasoning
        )
    
    def _generate_mathematical_numbers(self, historical_draws: List[DrawResult]) -> List[int]:
        """Generate numbers using combined mathematical algorithms."""
        
        # Step 1: Generate base entropy
        entropy = self._generate_entropy()
        
        # Step 2: Apply mathematical transformations
        candidates = []
        
        # Fibonacci-based candidates
        if self.config.use_fibonacci:
            fib_candidates = self._fibonacci_transform(entropy)
            candidates.extend(fib_candidates)
        
        # Prime-based candidates
        if self.config.use_prime_weights:
            prime_candidates = self._prime_transform(entropy)
            candidates.extend(prime_candidates)
        
        # Golden ratio-based candidates
        if self.config.use_golden_ratio:
            golden_candidates = self._golden_ratio_transform(entropy)
            candidates.extend(golden_candidates)
        
        # Chaos theory-based candidates
        if self.config.use_chaos_theory:
            chaos_candidates = self._chaos_transform(entropy)
            candidates.extend(chaos_candidates)
        
        # Step 3: Apply statistical bias correction
        if self.config.use_statistical_bias and historical_draws:
            candidates = self._apply_bias_correction(candidates, historical_draws)
        
        # Step 4: Select final 7 numbers
        final_numbers = self._select_final_numbers(candidates)
        
        return final_numbers

    def _generate_ml_hybrid_numbers(self, historical_draws: List[DrawResult]) -> List[int]:
        """Generate numbers using a hybrid ML and statistical approach."""

        # 1. Get ML predictions
        if not self.ml_predictor.is_trained:
            self.train_ml_model(historical_draws)
        
        ml_probs = self.ml_predictor.predict_probabilities(historical_draws)

        # 2. Get statistical scores (frequency and recency)
        freq_map = {}
        recency_map = {}
        for i, draw in enumerate(historical_draws):
            for num in draw.numbers:
                freq_map[num] = freq_map.get(num, 0) + 1
                recency_map[num] = i # Higher is more recent

        # 3. Calculate weighted scores for each number
        weighted_scores = {}
        for num in range(1, 51):
            # Normalize scores to be between 0 and 1
            freq_score = freq_map.get(num, 0) / len(historical_draws)
            recency_score = recency_map.get(num, 0) / len(historical_draws)
            ml_score = ml_probs.get(num, 0)

            # Combine scores with weights
            score = (0.3 * freq_score) + (0.3 * recency_score) + (0.4 * ml_score)
            weighted_scores[num] = score

        # 4. Select the top 7 numbers based on the weighted scores
        sorted_numbers = sorted(weighted_scores, key=weighted_scores.get, reverse=True)
        
        return sorted_numbers[:7]
    
    def _generate_chaos_numbers(self, historical_draws: List[DrawResult]) -> List[int]:
        """Generate numbers using chaos theory principles."""
        
        # Logistic map for chaos generation
        def logistic_map(x, r=3.9):
            return r * x * (1 - x)
        
        # Initialize with entropy
        entropy = self._generate_entropy()
        x = (entropy % 1000) / 1000.0  # Normalize to [0,1]
        
        numbers = []
        iterations = 0
        max_iterations = 1000
        
        while len(numbers) < 7 and iterations < max_iterations:
            # Apply logistic map
            x = logistic_map(x)
            
            # Transform to lottery number
            num = int(x * 49) + 1
            
            if num not in numbers and 1 <= num <= 50:
                numbers.append(num)
            
            iterations += 1
        
        # Fill remaining slots if needed
        while len(numbers) < 7:
            entropy = self._generate_entropy()
            num = (entropy % 49) + 1
            if num not in numbers:
                numbers.append(num)
        
        return numbers
    
    def _generate_fibonacci_numbers(self, historical_draws: List[DrawResult]) -> List[int]:
        """Generate numbers based on Fibonacci sequence properties."""
        
        numbers = []
        entropy = self._generate_entropy()
        
        # Use Fibonacci ratios for number selection
        for i in range(7):
            # Calculate position using Fibonacci ratio
            fib_ratio = self.fibonacci[i % len(self.fibonacci)] / self.fibonacci[-1]
            
            # Apply entropy and transform to lottery range
            base_num = int((fib_ratio * entropy) % 49) + 1
            
            # Ensure uniqueness
            while base_num in numbers:
                base_num = (base_num % 49) + 1
            
            numbers.append(base_num)
        
        return numbers
    
    def _generate_prime_numbers(self, historical_draws: List[DrawResult]) -> List[int]:
        """Generate numbers with prime number weighting."""
        
        numbers = []
        
        # Start with some prime numbers (but not all)
        available_primes = [p for p in self.primes if p <= 50]
        available_non_primes = [n for n in range(1, 51) if n not in self.primes]
        
        # Select 3-4 prime numbers
        entropy = self._generate_entropy()
        num_primes = 3 + (entropy % 2)  # 3 or 4 primes
        
        for i in range(num_primes):
            if available_primes:
                entropy = self._generate_entropy()
                idx = entropy % len(available_primes)
                selected_prime = available_primes.pop(idx)
                numbers.append(selected_prime)
        
        # Fill remaining slots with non-primes
        remaining_slots = 7 - len(numbers)
        for i in range(remaining_slots):
            if available_non_primes:
                entropy = self._generate_entropy()
                idx = entropy % len(available_non_primes)
                selected_non_prime = available_non_primes.pop(idx)
                numbers.append(selected_non_prime)
        
        # If we still need more numbers, use any remaining
        while len(numbers) < 7:
            all_remaining = [n for n in range(1, 51) if n not in numbers]
            if all_remaining:
                entropy = self._generate_entropy()
                idx = entropy % len(all_remaining)
                numbers.append(all_remaining[idx])
            else:
                break
        
        return numbers
    
    def _generate_entropy(self) -> int:
        """Generate high-quality entropy from multiple sources."""
        
        entropy_value = 0
        
        if 'time' in self.config.entropy_sources:
            # Time-based entropy
            current_time = time.time()
            time_entropy = int((current_time * 1000000) % 1000000)
            entropy_value ^= time_entropy
        
        if 'system' in self.config.entropy_sources:
            # System-based entropy (simulated)
            import os
            try:
                system_entropy = int.from_bytes(os.urandom(4), byteorder='big')
                entropy_value ^= system_entropy
            except:
                # Fallback if os.urandom not available
                system_entropy = hash(str(datetime.now())) % 1000000
                entropy_value ^= system_entropy
        
        if 'mathematical' in self.config.entropy_sources:
            # Mathematical entropy using transcendental numbers
            math_entropy = int((self.pi * self.euler_number * 1000000) % 1000000)
            entropy_value ^= math_entropy
        
        # Hash the combined entropy for better distribution
        entropy_hash = hashlib.sha256(str(entropy_value).encode()).hexdigest()
        final_entropy = int(entropy_hash[:8], 16)
        
        return final_entropy
    
    def _fibonacci_transform(self, entropy: int) -> List[int]:
        """Transform entropy using Fibonacci sequence."""
        candidates = []
        
        for i, fib in enumerate(self.fibonacci[:10]):  # Use first 10 Fibonacci numbers
            # Apply Fibonacci transformation
            transformed = ((entropy * fib) % 49) + 1
            if 1 <= transformed <= 50:
                candidates.append(transformed)
        
        return candidates
    
    def _prime_transform(self, entropy: int) -> List[int]:
        """Transform entropy using prime number properties."""
        candidates = []
        
        for prime in self.primes[:10]:  # Use first 10 primes
            # Apply prime transformation
            transformed = ((entropy % prime) * prime) % 49 + 1
            if 1 <= transformed <= 50:
                candidates.append(transformed)
        
        return candidates
    
    def _golden_ratio_transform(self, entropy: int) -> List[int]:
        """Transform entropy using golden ratio."""
        candidates = []
        
        for i in range(10):
            # Apply golden ratio transformation
            golden_factor = (self.golden_ratio ** i) % 1
            transformed = int((entropy * golden_factor) % 49) + 1
            if 1 <= transformed <= 50:
                candidates.append(transformed)
        
        return candidates
    
    def _chaos_transform(self, entropy: int) -> List[int]:
        """Transform entropy using chaos theory."""
        candidates = []
        
        # Henon map for chaos
        x, y = 0.1, 0.1
        a, b = 1.4, 0.3
        
        # Seed with entropy
        x = (entropy % 1000) / 1000.0
        
        for _ in range(20):
            x_new = 1 - a * x * x + y
            y_new = b * x
            x, y = x_new, y_new
            
            # Transform to lottery number
            num = int(abs(x * 49)) + 1
            if 1 <= num <= 50:
                candidates.append(num)
        
        return candidates
    
    def _apply_bias_correction(self, candidates: List[int], 
                             historical_draws: List[DrawResult]) -> List[int]:
        """Apply statistical bias correction based on historical data."""
        
        if not historical_draws:
            return candidates
        
        # Calculate historical frequencies
        freq_map = {}
        total_numbers = 0
        
        for draw in historical_draws:
            for num in draw.numbers:
                freq_map[num] = freq_map.get(num, 0) + 1
                total_numbers += 1
        
        # Calculate expected frequency
        expected_freq = total_numbers / 50 if total_numbers > 0 else 1
        
        # Apply bias correction to candidates
        corrected_candidates = []
        
        for candidate in candidates:
            actual_freq = freq_map.get(candidate, 0)
            
            # Calculate bias factor
            if actual_freq > expected_freq * 1.2:  # Over-represented
                # Reduce probability
                if np.random.random() > 0.7:  # 30% chance to include
                    corrected_candidates.append(candidate)
            elif actual_freq < expected_freq * 0.8:  # Under-represented
                # Increase probability
                corrected_candidates.append(candidate)
                if np.random.random() > 0.5:  # 50% chance to add twice
                    corrected_candidates.append(candidate)
            else:
                # Normal representation
                corrected_candidates.append(candidate)
        
        return corrected_candidates
    
    def _select_final_numbers(self, candidates: List[int]) -> List[int]:
        """Select final 7 numbers from candidates using mathematical criteria."""
        
        if len(candidates) < 7:
            # Not enough candidates, generate more
            while len(candidates) < 20:
                entropy = self._generate_entropy()
                num = (entropy % 49) + 1
                candidates.append(num)
        
        # Remove duplicates while preserving order
        unique_candidates = []
        seen = set()
        for candidate in candidates:
            if candidate not in seen and 1 <= candidate <= 50:
                unique_candidates.append(candidate)
                seen.add(candidate)
        
        if len(unique_candidates) < 7:
            # Still not enough, fill with systematic generation
            for i in range(1, 51):
                if i not in seen:
                    unique_candidates.append(i)
                if len(unique_candidates) >= 20:
                    break
        
        # Select 7 numbers using mathematical criteria
        final_numbers = []
        
        # Ensure good distribution across ranges
        ranges = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50)]
        numbers_per_range = [0, 0, 0, 0, 0]
        
        for candidate in unique_candidates:
            if len(final_numbers) >= 7:
                break
            
            # Determine range
            range_idx = (candidate - 1) // 10
            if range_idx >= 5:
                range_idx = 4
            
            # Check if we need more numbers from this range
            if numbers_per_range[range_idx] < 2:  # Max 2 per range
                final_numbers.append(candidate)
                numbers_per_range[range_idx] += 1
        
        # Fill remaining slots if needed
        while len(final_numbers) < 7:
            for candidate in unique_candidates:
                if candidate not in final_numbers:
                    final_numbers.append(candidate)
                    break
            else:
                # Generate a new number if all candidates exhausted
                entropy = self._generate_entropy()
                num = (entropy % 49) + 1
                if num not in final_numbers:
                    final_numbers.append(num)
        
        return final_numbers[:7]
    
    def _calculate_mathematical_confidence(self, numbers: List[int], 
                                        historical_draws: List[DrawResult]) -> float:
        """Calculate confidence based on mathematical properties."""
        
        confidence_factors = []
        
        # Factor 1: Distribution quality (0.0 - 1.0)
        ranges = [0, 0, 0, 0, 0]
        for num in numbers:
            range_idx = (num - 1) // 10
            if range_idx >= 5:
                range_idx = 4
            ranges[range_idx] += 1
        
        # Good distribution has numbers across multiple ranges
        non_zero_ranges = sum(1 for r in ranges if r > 0)
        distribution_score = non_zero_ranges / 5.0
        confidence_factors.append(distribution_score)
        
        # Factor 2: Mathematical properties
        # Check for prime numbers
        prime_count = sum(1 for num in numbers if num in self.primes)
        prime_score = min(prime_count / 3.0, 1.0)  # Optimal: 2-3 primes
        confidence_factors.append(prime_score)
        
        # Factor 3: Sum analysis
        total_sum = sum(numbers)
        expected_sum = 25.5 * 7  # Expected value for uniform distribution
        sum_deviation = abs(total_sum - expected_sum) / expected_sum
        sum_score = max(0, 1.0 - sum_deviation)
        confidence_factors.append(sum_score)
        
        # Factor 4: Odd/Even balance
        odd_count = sum(1 for num in numbers if num % 2 == 1)
        even_count = 7 - odd_count
        balance_score = 1.0 - abs(odd_count - even_count) / 7.0
        confidence_factors.append(balance_score)
        
        # Factor 5: Historical uniqueness (if historical data available)
        if historical_draws:
            # Check how often this exact combination appeared
            combination_set = set(numbers)
            matches = 0
            for draw in historical_draws[-100:]:  # Check last 100 draws
                draw_set = set(draw.numbers)
                if len(combination_set.intersection(draw_set)) >= 5:
                    matches += 1
            
            uniqueness_score = max(0, 1.0 - matches / 10.0)
            confidence_factors.append(uniqueness_score)
        
        # Calculate weighted average
        weights = [0.25, 0.15, 0.20, 0.15, 0.25] if historical_draws else [0.3, 0.2, 0.25, 0.25]
        
        confidence = sum(factor * weight for factor, weight in zip(confidence_factors, weights))
        
        # Add mathematical randomness bonus
        entropy_bonus = min(0.1, self._calculate_entropy_quality(numbers))
        confidence += entropy_bonus
        
        return min(confidence, 1.0)
    
    def _calculate_entropy_quality(self, numbers: List[int]) -> float:
        """Calculate the entropy quality of the number selection."""
        
        # Calculate Shannon entropy
        # For lottery numbers, we look at digit distribution
        digits = []
        for num in numbers:
            digits.extend([int(d) for d in str(num)])
        
        # Count digit frequencies
        digit_counts = [0] * 10
        for digit in digits:
            digit_counts[digit] += 1
        
        # Calculate entropy
        total_digits = len(digits)
        entropy = 0
        for count in digit_counts:
            if count > 0:
                p = count / total_digits
                entropy -= p * np.log2(p)
        
        # Normalize entropy (max entropy for 10 digits is log2(10))
        max_entropy = np.log2(10)
        normalized_entropy = entropy / max_entropy
        
        return normalized_entropy
    
    def _generate_primes(self, limit: int) -> List[int]:
        """Generate prime numbers up to limit using Sieve of Eratosthenes."""
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        
        for i in range(2, int(limit**0.5) + 1):
            if sieve[i]:
                for j in range(i*i, limit + 1, i):
                    sieve[j] = False
        
        return [i for i in range(2, limit + 1) if sieve[i]]
    
    def _generate_fibonacci(self, limit: int) -> List[int]:
        """Generate Fibonacci numbers up to limit."""
        fib = [1, 1]
        while fib[-1] < limit:
            fib.append(fib[-1] + fib[-2])
        return fib[:-1]  # Remove the last one that exceeds limit
    
    def _initialize_entropy_pool(self) -> Dict:
        """Initialize entropy pool with various sources."""
        return {
            'mathematical_constants': [self.pi, self.euler_number, self.golden_ratio],
            'prime_products': [p1 * p2 for p1 in self.primes[:5] for p2 in self.primes[:5] if p1 != p2],
            'fibonacci_ratios': [self.fibonacci[i+1] / self.fibonacci[i] for i in range(len(self.fibonacci)-1)]
        }