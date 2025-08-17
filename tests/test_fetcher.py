"""Unit tests for data fetching operations."""

import pytest
import requests
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from lotto_max_analyzer.data.fetcher import DataFetcher
from lotto_max_analyzer.data.models import DrawResult


class TestDataFetcher:
    """Test cases for DataFetcher class."""
    
    @pytest.fixture
    def fetcher(self):
        """Create a DataFetcher instance for testing."""
        return DataFetcher()
    
    @pytest.fixture
    def date_range(self):
        """Create a test date range."""
        end_date = datetime(2024, 1, 15)
        start_date = end_date - timedelta(days=14)  # 2 weeks
        return start_date, end_date
    
    def test_fetcher_initialization(self, fetcher):
        """Test that fetcher initializes properly."""
        assert fetcher.session is not None
        assert 'User-Agent' in fetcher.session.headers
        assert fetcher.base_url == "https://www.lotto649.com"
    
    def test_invalid_date_range(self, fetcher):
        """Test that invalid date ranges raise ValueError."""
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 10)  # End before start
        
        with pytest.raises(ValueError, match="Start date must be before end date"):
            fetcher.fetch_historical_data(start_date, end_date)
    
    def test_fetch_historical_data_mock_fallback(self, fetcher, date_range):
        """Test that fetcher falls back to mock data when sources fail."""
        start_date, end_date = date_range
        
        draws = fetcher.fetch_historical_data(start_date, end_date)
        
        # Should return mock data
        assert len(draws) > 0
        assert all(isinstance(draw, DrawResult) for draw in draws)
        
        # Verify draws are within date range
        for draw in draws:
            assert start_date <= draw.date <= end_date
    
    def test_fetch_latest_draw(self, fetcher):
        """Test fetching the latest draw."""
        latest_draw = fetcher.fetch_latest_draw()
        
        # Should return a DrawResult or None
        assert latest_draw is None or isinstance(latest_draw, DrawResult)
        
        # If a draw is returned, it should be recent
        if latest_draw:
            days_ago = (datetime.now() - latest_draw.date).days
            assert days_ago <= 7  # Within last week
    
    def test_create_mock_draw(self, fetcher):
        """Test mock draw creation."""
        test_date = datetime(2024, 1, 15)
        
        draw = fetcher._create_mock_draw(test_date)
        
        assert isinstance(draw, DrawResult)
        assert draw.date == test_date
        assert len(draw.numbers) == 7
        assert all(1 <= num <= 50 for num in draw.numbers)
        assert draw.numbers == sorted(draw.numbers)  # Should be sorted
        assert 1 <= draw.bonus <= 50
        assert draw.bonus not in draw.numbers  # Bonus should be unique
        assert draw.jackpot_amount > 0
        assert draw.draw_id == "2024-01-15"
    
    def test_generate_mock_data_draw_days(self, fetcher):
        """Test that mock data only generates for draw days (Tue/Fri)."""
        # Test a week that includes Tuesday (Jan 9) and Friday (Jan 12)
        start_date = datetime(2024, 1, 8)  # Monday
        end_date = datetime(2024, 1, 14)    # Sunday
        
        draws = fetcher._generate_mock_data(start_date, end_date)
        
        # Should have draws for Tuesday and Friday only
        assert len(draws) == 2
        
        draw_dates = [draw.date.weekday() for draw in draws]
        assert 1 in draw_dates  # Tuesday
        assert 4 in draw_dates  # Friday
    
    def test_validate_draw_data_valid(self, fetcher):
        """Test validation of valid draw data."""
        valid_data = {
            'date': datetime(2024, 1, 15),
            'numbers': [7, 14, 21, 28, 35, 42, 49],
            'bonus': 13,
            'jackpot': 75000000.0
        }
        
        assert fetcher._validate_draw_data(valid_data) is True
    
    def test_validate_draw_data_missing_fields(self, fetcher):
        """Test validation fails for missing required fields."""
        invalid_data = {
            'date': datetime(2024, 1, 15),
            'numbers': [7, 14, 21, 28, 35, 42, 49],
            # Missing bonus and jackpot
        }
        
        assert fetcher._validate_draw_data(invalid_data) is False
    
    def test_validate_draw_data_invalid_numbers(self, fetcher):
        """Test validation fails for invalid numbers."""
        # Wrong number count
        invalid_data1 = {
            'date': datetime(2024, 1, 15),
            'numbers': [7, 14, 21, 28, 35],  # Only 5 numbers
            'bonus': 13,
            'jackpot': 75000000.0
        }
        assert fetcher._validate_draw_data(invalid_data1) is False
        
        # Numbers out of range
        invalid_data2 = {
            'date': datetime(2024, 1, 15),
            'numbers': [7, 14, 21, 28, 35, 42, 51],  # 51 is out of range
            'bonus': 13,
            'jackpot': 75000000.0
        }
        assert fetcher._validate_draw_data(invalid_data2) is False
    
    def test_validate_draw_data_invalid_bonus(self, fetcher):
        """Test validation fails for invalid bonus number."""
        invalid_data = {
            'date': datetime(2024, 1, 15),
            'numbers': [7, 14, 21, 28, 35, 42, 49],
            'bonus': 0,  # Out of range
            'jackpot': 75000000.0
        }
        
        assert fetcher._validate_draw_data(invalid_data) is False
    
    def test_validate_draw_data_invalid_jackpot(self, fetcher):
        """Test validation fails for invalid jackpot amount."""
        invalid_data = {
            'date': datetime(2024, 1, 15),
            'numbers': [7, 14, 21, 28, 35, 42, 49],
            'bonus': 13,
            'jackpot': -1000000  # Negative jackpot
        }
        
        assert fetcher._validate_draw_data(invalid_data) is False
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get, fetcher):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = fetcher._make_request("http://example.com")
        
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_make_request_retry_logic(self, mock_get, fetcher):
        """Test request retry logic on failure."""
        # Mock failed requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(requests.RequestException):
            fetcher._make_request("http://example.com")
        
        # Should retry MAX_RETRIES times
        assert mock_get.call_count == 3  # MAX_RETRIES = 3
    
    def test_close_session(self, fetcher):
        """Test that session is properly closed."""
        # Mock the session close method
        fetcher.session.close = Mock()
        
        fetcher.close()
        
        fetcher.session.close.assert_called_once()
    
    def test_mock_data_uniqueness(self, fetcher):
        """Test that mock data generates unique draws."""
        start_date = datetime(2024, 1, 2)  # Tuesday
        end_date = datetime(2024, 1, 16)   # Tuesday (2 weeks)
        
        draws = fetcher._generate_mock_data(start_date, end_date)
        
        # Check that all draw IDs are unique
        draw_ids = [draw.draw_id for draw in draws]
        assert len(draw_ids) == len(set(draw_ids))
        
        # Check that number combinations are different
        number_combinations = [tuple(draw.numbers) for draw in draws]
        # While theoretically possible to have duplicates, it's extremely unlikely
        assert len(number_combinations) == len(set(number_combinations))
    
    def test_mock_data_realistic_jackpots(self, fetcher):
        """Test that mock jackpots are realistic."""
        draws = fetcher._generate_mock_data(
            datetime(2024, 1, 2), 
            datetime(2024, 1, 5)
        )
        
        for draw in draws:
            # Jackpots should be between 10M and 100M
            assert 10_000_000 <= draw.jackpot_amount <= 100_000_000
            # Should be rounded to nearest million
            assert draw.jackpot_amount % 1_000_000 == 0


if __name__ == "__main__":
    pytest.main([__file__])