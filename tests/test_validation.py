"""Unit tests for validation utilities."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from lotto_max_analyzer.utils.validation import DataValidator, ValidationError


class TestDataValidator:
    """Test cases for DataValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a DataValidator instance for testing."""
        return DataValidator()
    
    def test_validate_lotto_numbers_valid(self, validator):
        """Test validation of valid Lotto Max numbers."""
        numbers = [7, 14, 21, 28, 35, 42, 49]
        result = validator.validate_lotto_numbers(numbers)
        
        assert result == [7, 14, 21, 28, 35, 42, 49]
        assert len(result) == 7
        assert all(1 <= num <= 50 for num in result)
    
    def test_validate_lotto_numbers_wrong_count(self, validator):
        """Test validation fails with wrong number count."""
        numbers = [1, 2, 3, 4, 5]  # Only 5 numbers
        
        with pytest.raises(ValidationError, match="Must have exactly 7 numbers"):
            validator.validate_lotto_numbers(numbers)
    
    def test_validate_lotto_numbers_out_of_range(self, validator):
        """Test validation fails with numbers out of range."""
        numbers = [1, 2, 3, 4, 5, 6, 51]  # 51 is out of range
        
        with pytest.raises(ValidationError, match="must be between 1 and 50"):
            validator.validate_lotto_numbers(numbers)
    
    def test_validate_lotto_numbers_duplicates(self, validator):
        """Test validation fails with duplicate numbers."""
        numbers = [1, 2, 3, 4, 5, 6, 6]  # Duplicate 6
        
        with pytest.raises(ValidationError, match="Duplicate numbers found"):
            validator.validate_lotto_numbers(numbers)
    
    def test_validate_lotto_numbers_allow_duplicates(self, validator):
        """Test validation allows duplicates when specified."""
        numbers = [1, 2, 3, 4, 5, 6, 6]  # Duplicate 6
        
        result = validator.validate_lotto_numbers(numbers, allow_duplicates=True)
        assert len(result) == 7
    
    def test_validate_lotto_numbers_invalid_type(self, validator):
        """Test validation fails with invalid input type."""
        with pytest.raises(ValidationError, match="must be a list or tuple"):
            validator.validate_lotto_numbers("not a list")
    
    def test_validate_bonus_number_valid(self, validator):
        """Test validation of valid bonus number."""
        result = validator.validate_bonus_number(25)
        assert result == 25
    
    def test_validate_bonus_number_out_of_range(self, validator):
        """Test validation fails with bonus number out of range."""
        with pytest.raises(ValidationError, match="must be between 1 and 50"):
            validator.validate_bonus_number(0)
        
        with pytest.raises(ValidationError, match="must be between 1 and 50"):
            validator.validate_bonus_number(51)
    
    def test_validate_bonus_number_invalid_type(self, validator):
        """Test validation fails with invalid bonus number type."""
        with pytest.raises(ValidationError, match="not a valid integer"):
            validator.validate_bonus_number("not a number")
    
    def test_validate_jackpot_amount_valid(self, validator):
        """Test validation of valid jackpot amount."""
        result = validator.validate_jackpot_amount(75000000.0)
        assert result == 75000000.0
        
        # Test integer input
        result = validator.validate_jackpot_amount(50000000)
        assert result == 50000000.0
    
    def test_validate_jackpot_amount_negative(self, validator):
        """Test validation fails with negative jackpot."""
        with pytest.raises(ValidationError, match="cannot be negative"):
            validator.validate_jackpot_amount(-1000000)
    
    def test_validate_jackpot_amount_too_high(self, validator):
        """Test validation fails with unreasonably high jackpot."""
        with pytest.raises(ValidationError, match="unreasonably high"):
            validator.validate_jackpot_amount(2_000_000_000)  # 2 billion
    
    def test_validate_date_string_formats(self, validator):
        """Test validation of various date string formats."""
        test_cases = [
            ('2024-01-15', datetime(2024, 1, 15)),
            ('2024/01/15', datetime(2024, 1, 15)),
            ('01/15/2024', datetime(2024, 1, 15)),
        ]
        
        for date_str, expected in test_cases:
            result = validator.validate_date(date_str)
            assert result.date() == expected.date()
    
    def test_validate_date_datetime_object(self, validator):
        """Test validation of datetime object."""
        date_obj = datetime(2024, 1, 15)
        result = validator.validate_date(date_obj)
        assert result == date_obj
    
    def test_validate_date_invalid_format(self, validator):
        """Test validation fails with invalid date format."""
        with pytest.raises(ValidationError, match="Invalid date format"):
            validator.validate_date("not-a-date")
    
    def test_validate_date_too_early(self, validator):
        """Test validation fails with date before Lotto Max started."""
        with pytest.raises(ValidationError, match="before Lotto Max started"):
            validator.validate_date("2008-01-01")
    
    def test_validate_date_future_not_allowed(self, validator):
        """Test validation fails with future date when not allowed."""
        future_date = datetime.now() + timedelta(days=30)
        
        with pytest.raises(ValidationError, match="is in the future"):
            validator.validate_date(future_date, allow_future=False)
    
    def test_validate_date_future_allowed(self, validator):
        """Test validation succeeds with future date when allowed."""
        future_date = datetime.now() + timedelta(days=30)
        result = validator.validate_date(future_date, allow_future=True)
        assert result == future_date
    
    def test_validate_date_range_valid(self, validator):
        """Test validation of valid date range."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        result_start, result_end = validator.validate_date_range(start, end)
        assert result_start == start
        assert result_end == end
    
    def test_validate_date_range_invalid_order(self, validator):
        """Test validation fails with invalid date order."""
        start = datetime(2024, 12, 31)
        end = datetime(2024, 1, 1)
        
        with pytest.raises(ValidationError, match="must be before end date"):
            validator.validate_date_range(start, end)
    
    def test_validate_date_range_too_large(self, validator):
        """Test validation fails with date range too large."""
        start = datetime(2000, 1, 1)
        end = datetime(2025, 1, 1)  # 25 years
        
        with pytest.raises(ValidationError, match="Date range is too large"):
            validator.validate_date_range(start, end)
    
    def test_validate_draw_id_valid(self, validator):
        """Test validation of valid draw ID."""
        result = validator.validate_draw_id("2024-01-15")
        assert result == "2024-01-15"
        
        result = validator.validate_draw_id("  2024_001  ")  # With whitespace
        assert result == "2024_001"
    
    def test_validate_draw_id_empty(self, validator):
        """Test validation fails with empty draw ID."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validator.validate_draw_id("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            validator.validate_draw_id("   ")
    
    def test_validate_draw_id_too_long(self, validator):
        """Test validation fails with draw ID too long."""
        long_id = "a" * 51  # 51 characters
        
        with pytest.raises(ValidationError, match="too long"):
            validator.validate_draw_id(long_id)
    
    def test_validate_draw_id_invalid_characters(self, validator):
        """Test validation fails with invalid characters in draw ID."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validator.validate_draw_id("2024@01#15")
    
    def test_validate_file_path_valid(self, validator):
        """Test validation of valid file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "test_file.txt"
            
            result = validator.validate_file_path(test_path)
            assert isinstance(result, Path)
            assert result == test_path
    
    def test_validate_file_path_must_exist(self, validator):
        """Test validation fails when file must exist but doesn't."""
        non_existent = Path("non_existent_file.txt")
        
        with pytest.raises(ValidationError, match="does not exist"):
            validator.validate_file_path(non_existent, must_exist=True)
    
    def test_validate_strategy_valid(self, validator):
        """Test validation of valid strategy names."""
        valid_strategies = ['hot_numbers', 'cold_numbers', 'balanced', 'hot', 'cold', 'all']
        
        for strategy in valid_strategies:
            result = validator.validate_strategy(strategy)
            assert result == strategy.lower()
    
    def test_validate_strategy_invalid(self, validator):
        """Test validation fails with invalid strategy."""
        with pytest.raises(ValidationError, match="Invalid strategy"):
            validator.validate_strategy("invalid_strategy")
    
    def test_validate_confidence_score_valid(self, validator):
        """Test validation of valid confidence scores."""
        test_scores = [0.0, 0.5, 1.0, 0.75]
        
        for score in test_scores:
            result = validator.validate_confidence_score(score)
            assert result == float(score)
    
    def test_validate_confidence_score_out_of_range(self, validator):
        """Test validation fails with confidence score out of range."""
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            validator.validate_confidence_score(-0.1)
        
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            validator.validate_confidence_score(1.5)
    
    def test_validate_analysis_data_valid(self, validator):
        """Test validation of valid analysis data."""
        from lotto_max_analyzer.data.models import DrawResult
        
        draws = []
        for i in range(60):  # Enough for analysis
            draw = DrawResult(
                date=datetime(2024, 1, 1) + timedelta(days=i),
                numbers=[1, 2, 3, 4, 5, 6, 7],
                bonus=8,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        result = validator.validate_analysis_data(draws)
        assert len(result) == 60
    
    def test_validate_analysis_data_insufficient(self, validator):
        """Test validation fails with insufficient data."""
        draws = []  # Empty list
        
        with pytest.raises(ValidationError, match="Insufficient data for analysis"):
            validator.validate_analysis_data(draws)
    
    def test_sanitize_user_input_valid(self, validator):
        """Test sanitization of valid user input."""
        result = validator.sanitize_user_input("  Hello World  ")
        assert result == "Hello World"
    
    def test_sanitize_user_input_dangerous_chars(self, validator):
        """Test sanitization removes dangerous characters."""
        dangerous_input = "Hello<script>alert('xss')</script>World"
        result = validator.sanitize_user_input(dangerous_input)
        assert "<" not in result
        assert ">" not in result
        assert result == "Helloscriptalert(xss)/scriptWorld"
    
    def test_sanitize_user_input_too_long(self, validator):
        """Test sanitization fails with input too long."""
        long_input = "a" * 1001  # 1001 characters
        
        with pytest.raises(ValidationError, match="Input too long"):
            validator.sanitize_user_input(long_input)


if __name__ == "__main__":
    pytest.main([__file__])