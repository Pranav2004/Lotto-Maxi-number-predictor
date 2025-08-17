"""Unit tests for visualization components."""

import pytest
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tempfile
import os

from lotto_max_analyzer.visualization.charts import ChartGenerator
from lotto_max_analyzer.visualization.reports import ReportGenerator
from lotto_max_analyzer.data.models import DrawResult, Recommendation


class TestChartGenerator:
    """Test cases for ChartGenerator class."""
    
    @pytest.fixture
    def chart_generator(self):
        """Create a ChartGenerator instance for testing."""
        return ChartGenerator()
    
    @pytest.fixture
    def sample_frequency_data(self):
        """Create sample frequency data for testing."""
        return {i: 20 + (i % 10) for i in range(1, 51)}  # Varying frequencies
    
    @pytest.fixture
    def sample_draws(self):
        """Create sample draw results for testing."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(30):
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),
                numbers=[1, 2, 3, 4, 5, 6, 7] if i % 2 == 0 else [8, 9, 10, 11, 12, 13, 14],
                bonus=15,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        return draws
    
    @pytest.fixture
    def sample_pattern_summary(self):
        """Create sample pattern summary for testing."""
        from lotto_max_analyzer.data.models import Pattern
        
        return {
            'consecutive_patterns': [
                Pattern('consecutive', '2 consecutive numbers', 50, 0.8, [[1, 2], [3, 4]]),
                Pattern('consecutive', '3 consecutive numbers', 10, 0.6, [[1, 2, 3]])
            ],
            'odd_even_analysis': {
                'pattern_percentages': {'4-3': 40.0, '3-4': 35.0, '5-2': 15.0, '2-5': 10.0}
            },
            'range_analysis': {
                'percentages': {'low': 20.0, 'mid_low': 18.0, 'mid': 22.0, 'mid_high': 20.0, 'high': 20.0}
            },
            'sum_analysis': {
                'sum_distribution': {175: 5, 180: 8, 185: 12, 190: 10, 195: 5},
                'average_sum': 185.0
            },
            'pattern_score': 75.5
        }
    
    def test_chart_generator_initialization(self, chart_generator):
        """Test that chart generator initializes properly."""
        assert chart_generator.logger is not None
    
    def test_create_frequency_chart(self, chart_generator, sample_frequency_data):
        """Test frequency chart creation."""
        hot_numbers = [1, 2, 3, 4, 5]
        cold_numbers = [46, 47, 48, 49, 50]
        
        fig = chart_generator.create_frequency_chart(
            sample_frequency_data, hot_numbers, cold_numbers
        )
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 1
        
        ax = fig.axes[0]
        assert ax.get_xlabel() == 'Lotto Max Numbers'
        assert ax.get_ylabel() == 'Frequency Count'
        assert 'Number Frequency Distribution' in ax.get_title()
        
        plt.close(fig)
    
    def test_create_frequency_chart_no_highlights(self, chart_generator, sample_frequency_data):
        """Test frequency chart creation without hot/cold highlights."""
        fig = chart_generator.create_frequency_chart(sample_frequency_data)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 1
        
        plt.close(fig)
    
    def test_create_trend_chart(self, chart_generator, sample_draws):
        """Test trend chart creation."""
        numbers_to_track = [1, 2, 8, 9]
        
        fig = chart_generator.create_trend_chart(sample_draws, numbers_to_track)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 1
        
        ax = fig.axes[0]
        assert ax.get_xlabel() == 'Date'
        assert ax.get_ylabel() == 'Rolling Frequency (%)'
        assert 'Number Frequency Trends' in ax.get_title()
        
        plt.close(fig)
    
    def test_create_trend_chart_auto_numbers(self, chart_generator, sample_draws):
        """Test trend chart creation with automatic number selection."""
        fig = chart_generator.create_trend_chart(sample_draws)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 1
        
        plt.close(fig)
    
    def test_create_trend_chart_empty_draws(self, chart_generator):
        """Test trend chart creation with empty draws list."""
        with pytest.raises(ValueError, match="No draws provided"):
            chart_generator.create_trend_chart([])
    
    def test_create_pattern_visualization(self, chart_generator, sample_pattern_summary):
        """Test pattern visualization creation."""
        fig = chart_generator.create_pattern_visualization(sample_pattern_summary)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 4  # 2x2 subplot grid
        
        # Check that all subplots have titles
        for ax in fig.axes:
            assert ax.get_title() != ''
        
        plt.close(fig)
    
    def test_create_pattern_visualization_empty_data(self, chart_generator):
        """Test pattern visualization with empty data."""
        empty_summary = {
            'consecutive_patterns': [],
            'odd_even_analysis': {},
            'range_analysis': {},
            'sum_analysis': {}
        }
        
        fig = chart_generator.create_pattern_visualization(empty_summary)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 4
        
        plt.close(fig)
    
    def test_create_recommendation_comparison_chart(self, chart_generator, sample_frequency_data):
        """Test recommendation comparison chart creation."""
        recommendations = {
            'hot_numbers': [1, 2, 3, 4, 5, 6, 7],
            'cold_numbers': [44, 45, 46, 47, 48, 49, 50],
            'balanced': [1, 10, 20, 30, 40, 45, 50]
        }
        
        fig = chart_generator.create_recommendation_comparison_chart(
            recommendations, sample_frequency_data
        )
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) == 3  # 1x2 subplot grid + colorbar
        
        plt.close(fig)
    
    def test_create_comprehensive_dashboard(self, chart_generator, sample_draws, 
                                         sample_frequency_data, sample_pattern_summary):
        """Test comprehensive dashboard creation."""
        recommendations = {
            'hot_numbers': [1, 2, 3, 4, 5, 6, 7],
            'balanced': [1, 10, 20, 30, 40, 45, 50]
        }
        
        fig = chart_generator.create_comprehensive_dashboard(
            sample_draws, sample_frequency_data, sample_pattern_summary, recommendations
        )
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) >= 6  # Multiple subplots in dashboard
        
        plt.close(fig)
    
    def test_save_chart(self, chart_generator, sample_frequency_data):
        """Test chart saving functionality."""
        fig = chart_generator.create_frequency_chart(sample_frequency_data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, 'test_chart')
            
            saved_path = chart_generator.save_chart(fig, filename, 'png')
            
            assert saved_path == f"{filename}.png"
            assert os.path.exists(saved_path)
        
        plt.close(fig)
    
    def test_save_chart_different_formats(self, chart_generator, sample_frequency_data):
        """Test saving charts in different formats."""
        fig = chart_generator.create_frequency_chart(sample_frequency_data)
        
        formats = ['png', 'pdf', 'svg']
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for fmt in formats:
                filename = os.path.join(temp_dir, f'test_chart_{fmt}')
                
                saved_path = chart_generator.save_chart(fig, filename, fmt)
                
                assert saved_path == f"{filename}.{fmt}"
                assert os.path.exists(saved_path)
        
        plt.close(fig)


class TestReportGenerator:
    """Test cases for ReportGenerator class."""
    
    @pytest.fixture
    def report_generator(self):
        """Create a ReportGenerator instance for testing."""
        return ReportGenerator()
    
    @pytest.fixture
    def sample_draws(self):
        """Create sample draw results for testing."""
        draws = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(10):
            draw = DrawResult(
                date=base_date + timedelta(days=i * 3),
                numbers=[1, 2, 3, 4, 5, 6, 7],
                bonus=8,
                jackpot_amount=50000000.0,
                draw_id=f"2024-{i:03d}"
            )
            draws.append(draw)
        
        return draws
    
    @pytest.fixture
    def sample_frequency_data(self):
        """Create sample frequency data for testing."""
        return {i: 10 + (i % 5) for i in range(1, 51)}
    
    @pytest.fixture
    def sample_pattern_summary(self):
        """Create sample pattern summary for testing."""
        from lotto_max_analyzer.data.models import Pattern
        
        return {
            'total_draws': 100,
            'pattern_score': 85.5,
            'consecutive_patterns': [
                Pattern('consecutive', '2 consecutive numbers', 25, 0.7, [[1, 2], [5, 6]])
            ],
            'odd_even_analysis': {
                'average_odd_count': 3.5,
                'average_even_count': 3.5,
                'most_common_pattern': ('4-3', 30),
                'pattern_percentages': {'4-3': 35.0, '3-4': 30.0, '5-2': 20.0, '2-5': 15.0}
            },
            'range_analysis': {
                'range_balance_score': 78.5,
                'percentages': {'low': 22.0, 'mid_low': 19.0, 'mid': 20.0, 'mid_high': 19.0, 'high': 20.0},
                'average_per_draw': {'low': 1.5, 'mid_low': 1.3, 'mid': 1.4, 'mid_high': 1.3, 'high': 1.4}
            },
            'sum_analysis': {
                'average_sum': 178.5,
                'min_sum': 150,
                'max_sum': 210,
                'std_deviation': 15.2
            },
            'gap_analysis': {
                'average_gap': 8.2,
                'min_gap': 1,
                'max_gap': 25
            }
        }
    
    @pytest.fixture
    def sample_recommendations(self):
        """Create sample recommendations for testing."""
        return {
            'hot_numbers': Recommendation(
                strategy='hot_numbers',
                numbers=[1, 2, 3, 4, 5, 6, 7],
                confidence=0.75,
                rationale='Hot number strategy based on frequency analysis.'
            ),
            'cold_numbers': Recommendation(
                strategy='cold_numbers',
                numbers=[44, 45, 46, 47, 48, 49, 50],
                confidence=0.60,
                rationale='Cold number strategy targeting overdue numbers.'
            ),
            'balanced': Recommendation(
                strategy='balanced',
                numbers=[1, 10, 20, 30, 40, 45, 50],
                confidence=0.85,
                rationale='Balanced strategy combining multiple factors.'
            )
        }
    
    def test_report_generator_initialization(self, report_generator):
        """Test that report generator initializes properly."""
        assert report_generator.logger is not None
    
    def test_generate_frequency_report(self, report_generator, sample_draws, 
                                     sample_frequency_data):
        """Test frequency report generation."""
        hot_numbers = [1, 2, 3, 4, 5]
        cold_numbers = [46, 47, 48, 49, 50]
        
        report = report_generator.generate_frequency_report(
            sample_draws, sample_frequency_data, hot_numbers, cold_numbers
        )
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'FREQUENCY ANALYSIS REPORT' in report
        assert 'HOT NUMBERS' in report
        assert 'COLD NUMBERS' in report
        assert 'FREQUENCY RANKINGS' in report
        assert str(len(sample_draws)) in report
    
    def test_generate_frequency_report_empty_draws(self, report_generator):
        """Test frequency report generation with empty draws."""
        report = report_generator.generate_frequency_report([], {}, [], [])
        
        assert isinstance(report, str)
        assert 'No data available' in report
    
    def test_generate_pattern_report(self, report_generator, sample_pattern_summary):
        """Test pattern report generation."""
        report = report_generator.generate_pattern_report(sample_pattern_summary)
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'PATTERN ANALYSIS REPORT' in report
        assert 'CONSECUTIVE NUMBER PATTERNS' in report
        assert 'ODD/EVEN DISTRIBUTION' in report
        assert 'NUMBER RANGE DISTRIBUTION' in report
        assert 'NUMBER SUM ANALYSIS' in report
        assert 'NUMBER GAP ANALYSIS' in report
    
    def test_generate_recommendation_report(self, report_generator, sample_recommendations,
                                          sample_frequency_data):
        """Test recommendation report generation."""
        report = report_generator.generate_recommendation_report(
            sample_recommendations, sample_frequency_data
        )
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'RECOMMENDATION REPORT' in report
        assert 'Hot Numbers STRATEGY' in report
        assert 'Cold Numbers STRATEGY' in report
        assert 'Balanced STRATEGY' in report
        assert 'STRATEGY COMPARISON' in report
    
    def test_generate_recommendation_report_empty(self, report_generator):
        """Test recommendation report generation with empty recommendations."""
        report = report_generator.generate_recommendation_report({}, {})
        
        assert isinstance(report, str)
        assert 'No recommendations available' in report
    
    def test_generate_comprehensive_report(self, report_generator, sample_draws,
                                         sample_frequency_data, sample_pattern_summary,
                                         sample_recommendations):
        """Test comprehensive report generation."""
        hot_numbers = [1, 2, 3, 4, 5]
        cold_numbers = [46, 47, 48, 49, 50]
        
        report = report_generator.generate_comprehensive_report(
            sample_draws, sample_frequency_data, sample_pattern_summary,
            sample_recommendations, hot_numbers, cold_numbers
        )
        
        assert isinstance(report, str)
        assert len(report) > 0
        assert 'COMPREHENSIVE ANALYSIS REPORT' in report
        assert 'EXECUTIVE SUMMARY' in report
        assert 'FREQUENCY ANALYSIS REPORT' in report
        assert 'PATTERN ANALYSIS REPORT' in report
        assert 'RECOMMENDATION REPORT' in report
        assert 'END OF REPORT' in report
    
    def test_save_report(self, report_generator):
        """Test report saving functionality."""
        test_content = "This is a test report content."
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, 'test_report')
            
            saved_path = report_generator.save_report(test_content, filename)
            
            assert saved_path == f"{filename}.txt"
            assert os.path.exists(saved_path)
            
            # Verify content
            with open(saved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert content == test_content
    
    def test_report_content_structure(self, report_generator, sample_draws,
                                    sample_frequency_data):
        """Test that reports have proper structure and formatting."""
        hot_numbers = [1, 2, 3]
        cold_numbers = [48, 49, 50]
        
        report = report_generator.generate_frequency_report(
            sample_draws, sample_frequency_data, hot_numbers, cold_numbers
        )
        
        lines = report.split('\n')
        
        # Check for proper section headers
        assert any('=' * 80 in line for line in lines)
        assert any('-' * 40 in line for line in lines)
        
        # Check for key sections
        assert any('ANALYSIS SUMMARY' in line for line in lines)
        assert any('HOT NUMBERS' in line for line in lines)
        assert any('COLD NUMBERS' in line for line in lines)
    
    def test_report_number_formatting(self, report_generator, sample_draws,
                                    sample_frequency_data):
        """Test that numbers are properly formatted in reports."""
        report = report_generator.generate_frequency_report(
            sample_draws, sample_frequency_data, [1, 2], [49, 50]
        )
        
        # Check for proper number formatting (should have consistent spacing)
        lines = report.split('\n')
        number_lines = [line for line in lines if 'Number' in line and ':' in line]
        
        assert len(number_lines) > 0
        
        # Check that percentages are formatted properly
        percentage_lines = [line for line in lines if '%' in line]
        assert len(percentage_lines) > 0


if __name__ == "__main__":
    pytest.main([__file__])