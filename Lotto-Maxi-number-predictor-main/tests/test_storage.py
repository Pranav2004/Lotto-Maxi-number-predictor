"""Unit tests for data storage operations."""

import pytest
import tempfile
import sqlite3
from datetime import datetime
from pathlib import Path

from lotto_max_analyzer.data.storage import DataStorage
from lotto_max_analyzer.data.models import DrawResult


class TestDataStorage:
    """Test cases for DataStorage class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        storage = DataStorage(db_path)
        yield storage
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def sample_draws(self):
        """Create sample draw results for testing."""
        return [
            DrawResult(
                date=datetime(2024, 1, 15),
                numbers=[7, 14, 21, 28, 35, 42, 49],
                bonus=13,
                jackpot_amount=75000000.0,
                draw_id="2024-01-15"
            ),
            DrawResult(
                date=datetime(2024, 1, 12),
                numbers=[3, 9, 18, 27, 33, 41, 47],
                bonus=22,
                jackpot_amount=70000000.0,
                draw_id="2024-01-12"
            ),
            DrawResult(
                date=datetime(2024, 1, 9),
                numbers=[1, 8, 15, 23, 31, 39, 45],
                bonus=17,
                jackpot_amount=65000000.0,
                draw_id="2024-01-09"
            )
        ]
    
    def test_database_initialization(self, temp_db):
        """Test that database and tables are created properly."""
        # Check that database file exists
        assert temp_db.db_path.exists()
        
        # Check that tables exist
        with temp_db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='draws'"
            )
            assert cursor.fetchone() is not None
    
    def test_save_single_draw(self, temp_db, sample_draws):
        """Test saving a single draw result."""
        draw = sample_draws[0]
        saved_count = temp_db.save_draws([draw])
        
        assert saved_count == 1
        assert temp_db.get_draw_count() == 1
    
    def test_save_multiple_draws(self, temp_db, sample_draws):
        """Test saving multiple draw results."""
        saved_count = temp_db.save_draws(sample_draws)
        
        assert saved_count == 3
        assert temp_db.get_draw_count() == 3
    
    def test_save_duplicate_draw(self, temp_db, sample_draws):
        """Test that duplicate draws are handled properly."""
        draw = sample_draws[0]
        
        # Save the same draw twice
        temp_db.save_draws([draw])
        saved_count = temp_db.save_draws([draw])
        
        # Second save should skip the duplicate
        assert saved_count == 0
        assert temp_db.get_draw_count() == 1
    
    def test_save_empty_draws_list(self, temp_db):
        """Test that saving empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot save empty draws list"):
            temp_db.save_draws([])
    
    def test_load_all_draws(self, temp_db, sample_draws):
        """Test loading all draws from database."""
        temp_db.save_draws(sample_draws)
        
        loaded_draws = temp_db.get_all_draws()
        
        assert len(loaded_draws) == 3
        # Should be ordered by date descending
        assert loaded_draws[0].date > loaded_draws[1].date > loaded_draws[2].date
    
    def test_load_draws_with_date_filter(self, temp_db, sample_draws):
        """Test loading draws with date range filtering."""
        temp_db.save_draws(sample_draws)
        
        # Load draws from Jan 10 onwards
        start_date = datetime(2024, 1, 10)
        filtered_draws = temp_db.load_draws(start_date=start_date)
        
        assert len(filtered_draws) == 2
        for draw in filtered_draws:
            assert draw.date >= start_date
    
    def test_get_draw_by_id(self, temp_db, sample_draws):
        """Test retrieving a specific draw by ID."""
        temp_db.save_draws(sample_draws)
        
        draw = temp_db.get_draw_by_id("2024-01-15")
        
        assert draw is not None
        assert draw.draw_id == "2024-01-15"
        assert draw.jackpot_amount == 75000000.0
    
    def test_get_nonexistent_draw_by_id(self, temp_db):
        """Test retrieving a non-existent draw returns None."""
        draw = temp_db.get_draw_by_id("nonexistent")
        assert draw is None
    
    def test_get_latest_draw(self, temp_db, sample_draws):
        """Test getting the most recent draw."""
        temp_db.save_draws(sample_draws)
        
        latest = temp_db.get_latest_draw()
        
        assert latest is not None
        assert latest.draw_id == "2024-01-15"  # Most recent date
    
    def test_get_latest_draw_empty_db(self, temp_db):
        """Test getting latest draw from empty database."""
        latest = temp_db.get_latest_draw()
        assert latest is None
    
    def test_delete_draw(self, temp_db, sample_draws):
        """Test deleting a draw by ID."""
        temp_db.save_draws(sample_draws)
        
        # Delete one draw
        deleted = temp_db.delete_draw("2024-01-12")
        
        assert deleted is True
        assert temp_db.get_draw_count() == 2
        assert temp_db.get_draw_by_id("2024-01-12") is None
    
    def test_delete_nonexistent_draw(self, temp_db):
        """Test deleting a non-existent draw."""
        deleted = temp_db.delete_draw("nonexistent")
        assert deleted is False
    
    def test_numbers_are_sorted(self, temp_db):
        """Test that numbers are stored in sorted order."""
        # Create draw with unsorted numbers
        draw = DrawResult(
            date=datetime(2024, 1, 15),
            numbers=[49, 7, 35, 14, 28, 42, 21],  # Unsorted
            bonus=13,
            jackpot_amount=75000000.0,
            draw_id="2024-01-15"
        )
        
        temp_db.save_draws([draw])
        loaded_draw = temp_db.get_draw_by_id("2024-01-15")
        
        # Numbers should be sorted when loaded
        assert loaded_draw.numbers == [7, 14, 21, 28, 35, 42, 49]
    
    def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        # Try to create storage with invalid path
        invalid_path = Path("/invalid/path/database.db")
        
        with pytest.raises(Exception):
            DataStorage(invalid_path)


if __name__ == "__main__":
    pytest.main([__file__])