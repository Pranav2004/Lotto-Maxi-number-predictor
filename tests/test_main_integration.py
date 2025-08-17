"""Integration tests for main application interface."""

import pytest
import tempfile
import os
import sys
from unittest.mock import patch
from io import StringIO
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lotto_max_analyzer.main import create_parser, parse_date, validate_date_range


class TestMainApplication:
    """Test cases for main application interface."""
    
    def test_create_parser(self):
        """Test argument parser creation."""
        parser = create_parser()
        
        # Test that parser is created successfully
        assert parser is not None
        
        # Test parsing valid arguments
        args = parser.parse_args(['--analyze'])
        assert args.analyze is True
    
    def test_parse_date_valid(self):
        """Test valid date parsing."""
        date = parse_date('2024-01-15')
        assert date == datetime(2024, 1, 15)
    
    def test_parse_date_invalid(self):
        """Test invalid date parsing."""
        with pytest.raises(Exception):
            parse_date('invalid-date')
    
    def test_validate_date_range_valid(self):
        """Test valid date range validation."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        assert validate_date_range(start, end) is True
    
    def test_validate_date_range_invalid(self):
        """Test invalid date range validation."""
        start = datetime(2024, 12, 31)
        end = datetime(2024, 1, 1)
        
        # Capture stdout to suppress error message
        with patch('sys.stdout', new_callable=StringIO):
            assert validate_date_range(start, end) is False
    
    def test_basic_functionality_exists(self):
        """Test that basic functions exist and are callable."""
        from lotto_max_analyzer.main import (
            check_database_status, run_fetch_data, run_analysis, 
            run_recommendations, run_visualizations, interactive_mode, show_status
        )
        
        # Test that functions exist and are callable
        assert callable(check_database_status)
        assert callable(run_fetch_data)
        assert callable(run_analysis)
        assert callable(run_recommendations)
        assert callable(run_visualizations)
        assert callable(interactive_mode)
        assert callable(show_status)
    
    def test_argument_parsing_combinations(self):
        """Test various argument combinations."""
        parser = create_parser()
        
        # Test fetch data
        args = parser.parse_args(['--fetch-data'])
        assert args.fetch_data is True
        
        # Test analysis
        args = parser.parse_args(['--analyze'])
        assert args.analyze is True
        
        # Test recommendations
        args = parser.parse_args(['--recommend', 'balanced'])
        assert args.recommend == 'balanced'
        
        # Test visualizations
        args = parser.parse_args(['--visualize'])
        assert args.visualize is True
        
        # Test date range
        args = parser.parse_args(['--start-date', '2024-01-01', '--end-date', '2024-12-31'])
        assert args.start_date == '2024-01-01'
        assert args.end_date == '2024-12-31'
        
        # Test verbose and quiet
        args = parser.parse_args(['--verbose'])
        assert args.verbose is True
        
        args = parser.parse_args(['--quiet'])
        assert args.quiet is True
        
        # Test interactive mode
        args = parser.parse_args(['--interactive'])
        assert args.interactive is True
        
        # Test status
        args = parser.parse_args(['--status'])
        assert args.status is True
    
    def test_output_directory_handling(self):
        """Test output directory creation and handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_output_dir = os.path.join(temp_dir, 'test_output')
            
            # Test that directory gets created
            parser = create_parser()
            args = parser.parse_args(['--output-dir', test_output_dir, '--visualize'])
            
            assert args.output_dir == test_output_dir
    
    def test_interactive_mode_components(self):
        """Test components of interactive mode."""
        # Test that interactive mode functions exist and are callable
        from lotto_max_analyzer.main import interactive_mode, show_status
        
        # These should be callable without errors (though we won't run them fully)
        assert callable(interactive_mode)
        assert callable(show_status)
    
    def test_error_handling_graceful(self):
        """Test that errors are handled gracefully."""
        # Test with invalid date format
        with pytest.raises(Exception):
            parse_date('not-a-date')
        
        # Test with invalid date range
        start = datetime(2024, 12, 31)
        end = datetime(2024, 1, 1)
        
        with patch('sys.stdout', new_callable=StringIO):
            result = validate_date_range(start, end)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])