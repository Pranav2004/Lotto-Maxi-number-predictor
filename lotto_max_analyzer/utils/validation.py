"""Comprehensive data validation utilities for Lotto Max Analyzer."""

import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from ..config import (
    LOTTO_MAX_MIN_NUMBER, LOTTO_MAX_MAX_NUMBER, 
    LOTTO_MAX_NUMBERS_COUNT, MIN_DRAWS_FOR_ANALYSIS
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidator:
    """Comprehensive data validation for all Lotto Max operations."""
    
    def __init__(self):
        """Initialize the data validator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_lotto_numbers(self, numbers: List[int], allow_duplicates: bool = False) -> List[int]:
        """
        Validate Lotto Max numbers.
        
        Args:
            numbers: List of numbers to validate
            allow_duplicates: Whether to allow duplicate numbers
            
        Returns:
            Validated and sorted list of numbers
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(numbers, (list, tuple)):
            raise ValidationError(f"Numbers must be a list or tuple, got {type(numbers)}")
        
        if len(numbers) != LOTTO_MAX_NUMBERS_COUNT:
            raise ValidationError(
                f"Must have exactly {LOTTO_MAX_NUMBERS_COUNT} numbers, got {len(numbers)}"
            )
        
        validated_numbers = []
        for i, num in enumerate(numbers):
            if not isinstance(num, int):
                try:
                    num = int(num)
                except (ValueError, TypeError):
                    raise ValidationError(f"Number at position {i+1} is not a valid integer: {num}")
            
            if not (LOTTO_MAX_MIN_NUMBER <= num <= LOTTO_MAX_MAX_NUMBER):
                raise ValidationError(
                    f"Number {num} at position {i+1} must be between "
                    f"{LOTTO_MAX_MIN_NUMBER} and {LOTTO_MAX_MAX_NUMBER}"
                )
            
            validated_numbers.append(num)
        
        if not allow_duplicates and len(set(validated_numbers)) != len(validated_numbers):
            duplicates = [num for num in validated_numbers if validated_numbers.count(num) > 1]
            raise ValidationError(f"Duplicate numbers found: {list(set(duplicates))}")
        
        return sorted(validated_numbers)
    
    def validate_bonus_number(self, bonus: int) -> int:
        """
        Validate bonus number.
        
        Args:
            bonus: Bonus number to validate
            
        Returns:
            Validated bonus number
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(bonus, int):
            try:
                bonus = int(bonus)
            except (ValueError, TypeError):
                raise ValidationError(f"Bonus number is not a valid integer: {bonus}")
        
        if not (LOTTO_MAX_MIN_NUMBER <= bonus <= LOTTO_MAX_MAX_NUMBER):
            raise ValidationError(
                f"Bonus number {bonus} must be between "
                f"{LOTTO_MAX_MIN_NUMBER} and {LOTTO_MAX_MAX_NUMBER}"
            )
        
        return bonus
    
    def validate_jackpot_amount(self, amount: Union[int, float]) -> float:
        """
        Validate jackpot amount.
        
        Args:
            amount: Jackpot amount to validate
            
        Returns:
            Validated jackpot amount
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(amount, (int, float)):
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                raise ValidationError(f"Jackpot amount is not a valid number: {amount}")
        
        if amount < 0:
            raise ValidationError(f"Jackpot amount cannot be negative: {amount}")
        
        # Check for reasonable upper bound (1 billion)
        if amount > 1_000_000_000:
            raise ValidationError(f"Jackpot amount seems unreasonably high: ${amount:,.0f}")
        
        return float(amount)
    
    def validate_date(self, date: Union[str, datetime], allow_future: bool = False) -> datetime:
        """
        Validate date input.
        
        Args:
            date: Date to validate (string or datetime)
            allow_future: Whether to allow future dates
            
        Returns:
            Validated datetime object
            
        Raises:
            ValidationError: If validation fails
        """
        if isinstance(date, str):
            # Try common date formats
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            parsed_date = None
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                raise ValidationError(
                    f"Invalid date format: {date}. "
                    f"Expected formats: YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY, DD/MM/YYYY"
                )
            
            date = parsed_date
        
        elif not isinstance(date, datetime):
            raise ValidationError(f"Date must be string or datetime object, got {type(date)}")
        
        # Check for reasonable date range (Lotto Max started in 2009)
        min_date = datetime(2009, 1, 1)
        if date < min_date:
            raise ValidationError(f"Date {date.strftime('%Y-%m-%d')} is before Lotto Max started (2009)")
        
        if not allow_future and date > datetime.now():
            raise ValidationError(f"Date {date.strftime('%Y-%m-%d')} is in the future")
        
        return date
    
    def validate_date_range(self, start_date: datetime, end_date: datetime) -> Tuple[datetime, datetime]:
        """
        Validate date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Tuple of validated start and end dates
            
        Raises:
            ValidationError: If validation fails
        """
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date, allow_future=True)
        
        if start_date >= end_date:
            raise ValidationError(
                f"Start date ({start_date.strftime('%Y-%m-%d')}) "
                f"must be before end date ({end_date.strftime('%Y-%m-%d')})"
            )
        
        # Check for reasonable range (max 20 years)
        max_range = timedelta(days=365 * 20)
        if (end_date - start_date) > max_range:
            raise ValidationError(
                f"Date range is too large: {(end_date - start_date).days} days. "
                f"Maximum allowed: {max_range.days} days"
            )
        
        return start_date, end_date
    
    def validate_draw_id(self, draw_id: str) -> str:
        """
        Validate draw ID format.
        
        Args:
            draw_id: Draw ID to validate
            
        Returns:
            Validated draw ID
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(draw_id, str):
            raise ValidationError(f"Draw ID must be a string, got {type(draw_id)}")
        
        if not draw_id.strip():
            raise ValidationError("Draw ID cannot be empty")
        
        # Check for reasonable length
        if len(draw_id) > 50:
            raise ValidationError(f"Draw ID is too long: {len(draw_id)} characters (max 50)")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', draw_id):
            raise ValidationError(
                f"Draw ID contains invalid characters: {draw_id}. "
                f"Only letters, numbers, hyphens, and underscores allowed"
            )
        
        return draw_id.strip()
    
    def validate_file_path(self, path: Union[str, Path], must_exist: bool = False, 
                          must_be_writable: bool = False) -> Path:
        """
        Validate file path.
        
        Args:
            path: File path to validate
            must_exist: Whether the file must already exist
            must_be_writable: Whether the path must be writable
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If validation fails
        """
        if isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            raise ValidationError(f"Path must be string or Path object, got {type(path)}")
        
        if must_exist and not path.exists():
            raise ValidationError(f"File does not exist: {path}")
        
        if must_be_writable:
            # Check if parent directory is writable
            parent = path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ValidationError(f"Cannot create directory {parent}: {e}")
            
            if not parent.is_dir():
                raise ValidationError(f"Parent path is not a directory: {parent}")
            
            # Try to create a test file to check writability
            test_file = parent / f".test_write_{datetime.now().timestamp()}"
            try:
                test_file.touch()
                test_file.unlink()
            except OSError as e:
                raise ValidationError(f"Directory is not writable: {parent} ({e})")
        
        return path
    
    def validate_strategy(self, strategy: str) -> str:
        """
        Validate recommendation strategy.
        
        Args:
            strategy: Strategy name to validate
            
        Returns:
            Validated strategy name
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(strategy, str):
            raise ValidationError(f"Strategy must be a string, got {type(strategy)}")
        
        strategy = strategy.strip().lower()
        
        valid_strategies = ['hot_numbers', 'cold_numbers', 'balanced', 'hot', 'cold', 'all']
        if strategy not in valid_strategies:
            raise ValidationError(
                f"Invalid strategy: {strategy}. "
                f"Valid options: {', '.join(valid_strategies)}"
            )
        
        return strategy
    
    def validate_confidence_score(self, confidence: float) -> float:
        """
        Validate confidence score.
        
        Args:
            confidence: Confidence score to validate
            
        Returns:
            Validated confidence score
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(confidence, (int, float)):
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                raise ValidationError(f"Confidence must be a number, got {type(confidence)}")
        
        if not (0 <= confidence <= 1):
            raise ValidationError(f"Confidence must be between 0 and 1, got {confidence}")
        
        return float(confidence)
    
    def validate_analysis_data(self, draws: List[Any], min_draws: Optional[int] = None) -> List[Any]:
        """
        Validate data for analysis operations.
        
        Args:
            draws: List of draw results
            min_draws: Minimum number of draws required
            
        Returns:
            Validated draws list
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(draws, (list, tuple)):
            raise ValidationError(f"Draws must be a list or tuple, got {type(draws)}")
        
        if not draws:
            raise ValidationError("No draws provided for analysis")
        
        min_required = min_draws or MIN_DRAWS_FOR_ANALYSIS
        if len(draws) < min_required:
            raise ValidationError(
                f"Insufficient data for analysis: {len(draws)} draws provided, "
                f"minimum {min_required} required"
            )
        
        return list(draws)
    
    def validate_frequency_data(self, frequency_data: Dict[int, int]) -> Dict[int, int]:
        """
        Validate frequency data structure.
        
        Args:
            frequency_data: Dictionary mapping numbers to frequencies
            
        Returns:
            Validated frequency data
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(frequency_data, dict):
            raise ValidationError(f"Frequency data must be a dictionary, got {type(frequency_data)}")
        
        if not frequency_data:
            raise ValidationError("Frequency data cannot be empty")
        
        validated_data = {}
        for number, frequency in frequency_data.items():
            # Validate number
            if not isinstance(number, int):
                try:
                    number = int(number)
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid number in frequency data: {number}")
            
            if not (LOTTO_MAX_MIN_NUMBER <= number <= LOTTO_MAX_MAX_NUMBER):
                raise ValidationError(f"Number {number} out of valid range")
            
            # Validate frequency
            if not isinstance(frequency, int):
                try:
                    frequency = int(frequency)
                except (ValueError, TypeError):
                    raise ValidationError(f"Invalid frequency for number {number}: {frequency}")
            
            if frequency < 0:
                raise ValidationError(f"Frequency cannot be negative for number {number}: {frequency}")
            
            validated_data[number] = frequency
        
        return validated_data
    
    def sanitize_user_input(self, user_input: str, max_length: int = 1000) -> str:
        """
        Sanitize user input for safety.
        
        Args:
            user_input: Raw user input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized input
            
        Raises:
            ValidationError: If input is invalid
        """
        if not isinstance(user_input, str):
            raise ValidationError(f"User input must be a string, got {type(user_input)}")
        
        # Strip whitespace
        sanitized = user_input.strip()
        
        # Check length
        if len(sanitized) > max_length:
            raise ValidationError(f"Input too long: {len(sanitized)} characters (max {max_length})")
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', '"', "'", '`', '\x00']
        for char in dangerous_chars:
            if char in sanitized:
                sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    def validate_output_format(self, format_type: str) -> str:
        """
        Validate output format type.
        
        Args:
            format_type: Format type to validate
            
        Returns:
            Validated format type
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(format_type, str):
            raise ValidationError(f"Format type must be a string, got {type(format_type)}")
        
        format_type = format_type.strip().lower()
        
        valid_formats = ['png', 'pdf', 'svg', 'txt', 'csv', 'json']
        if format_type not in valid_formats:
            raise ValidationError(
                f"Invalid format: {format_type}. "
                f"Valid options: {', '.join(valid_formats)}"
            )
        
        return format_type


# Global validator instance
validator = DataValidator()


def validate_lotto_numbers(numbers: List[int], allow_duplicates: bool = False) -> List[int]:
    """Convenience function for validating Lotto Max numbers."""
    return validator.validate_lotto_numbers(numbers, allow_duplicates)


def validate_date_range(start_date: datetime, end_date: datetime) -> Tuple[datetime, datetime]:
    """Convenience function for validating date ranges."""
    return validator.validate_date_range(start_date, end_date)


def validate_analysis_data(draws: List[Any], min_draws: Optional[int] = None) -> List[Any]:
    """Convenience function for validating analysis data."""
    return validator.validate_analysis_data(draws, min_draws)