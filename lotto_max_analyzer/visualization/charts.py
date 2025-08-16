"""Chart generation module for Lotto Max analysis."""

import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import numpy as np

from ..data.models import DrawResult
from ..config import (
    CHART_WIDTH, CHART_HEIGHT, CHART_DPI,
    COLOR_HOT, COLOR_COLD, COLOR_NEUTRAL,
    NUMBER_RANGES
)


class ChartGenerator:
    """Generates charts and visualizations for Lotto Max analysis."""
    
    def __init__(self):
        """Initialize the chart generator."""
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (CHART_WIDTH, CHART_HEIGHT)
        plt.rcParams['figure.dpi'] = CHART_DPI
        plt.rcParams['font.size'] = 10
    
    def create_frequency_chart(self, frequency_data: Dict[int, int], 
                             hot_numbers: Optional[List[int]] = None,
                             cold_numbers: Optional[List[int]] = None) -> plt.Figure:
        """
        Create a bar chart showing number frequency distribution.
        
        Args:
            frequency_data: Dictionary mapping numbers to frequency counts
            hot_numbers: List of hot numbers to highlight
            cold_numbers: List of cold numbers to highlight
            
        Returns:
            matplotlib Figure object
        """
        self.logger.info("Creating frequency chart")
        
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Prepare data
        numbers = list(range(1, 51))
        frequencies = [frequency_data.get(num, 0) for num in numbers]
        
        # Determine colors for each bar
        colors = []
        for num in numbers:
            if hot_numbers and num in hot_numbers:
                colors.append(COLOR_HOT)
            elif cold_numbers and num in cold_numbers:
                colors.append(COLOR_COLD)
            else:
                colors.append(COLOR_NEUTRAL)
        
        # Create bar chart
        bars = ax.bar(numbers, frequencies, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Customize chart
        ax.set_xlabel('Lotto Max Numbers')
        ax.set_ylabel('Frequency Count')
        ax.set_title('Number Frequency Distribution', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 51)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add legend
        legend_elements = []
        if hot_numbers:
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=COLOR_HOT, label='Hot Numbers'))
        if cold_numbers:
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=COLOR_COLD, label='Cold Numbers'))
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=COLOR_NEUTRAL, label='Other Numbers'))
        
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Add statistics text
        total_draws = sum(frequencies) // 7  # Assuming 7 numbers per draw
        avg_frequency = np.mean(frequencies)
        max_frequency = max(frequencies)
        min_frequency = min(frequencies)
        
        stats_text = f'Total Draws: {total_draws}\nAvg Frequency: {avg_frequency:.1f}\nRange: {min_frequency}-{max_frequency}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return fig
    
    def create_trend_chart(self, draws: List[DrawResult], 
                          numbers_to_track: Optional[List[int]] = None) -> plt.Figure:
        """
        Create a time-series chart showing number frequency trends over time.
        
        Args:
            draws: List of DrawResult objects
            numbers_to_track: Specific numbers to highlight in the trend
            
        Returns:
            matplotlib Figure object
        """
        self.logger.info("Creating trend chart")
        
        if not draws:
            raise ValueError("No draws provided for trend analysis")
        
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Sort draws by date
        sorted_draws = sorted(draws, key=lambda d: d.date)
        
        # If no specific numbers provided, track top 5 most frequent
        if numbers_to_track is None:
            frequency_count = defaultdict(int)
            for draw in sorted_draws:
                for num in draw.numbers:
                    frequency_count[num] += 1
            
            numbers_to_track = sorted(frequency_count.items(), key=lambda x: x[1], reverse=True)[:5]
            numbers_to_track = [num for num, _ in numbers_to_track]
        
        # Calculate rolling frequency for each tracked number
        window_size = max(10, len(sorted_draws) // 20)  # Adaptive window size
        
        for i, number in enumerate(numbers_to_track):
            dates = []
            rolling_frequencies = []
            
            for j in range(window_size, len(sorted_draws)):
                window_draws = sorted_draws[j-window_size:j]
                frequency = sum(1 for draw in window_draws if number in draw.numbers)
                rolling_frequency = (frequency / window_size) * 100  # Percentage
                
                dates.append(window_draws[-1].date)
                rolling_frequencies.append(rolling_frequency)
            
            # Plot line for this number
            color = plt.cm.tab10(i)  # Use different colors for each line
            ax.plot(dates, rolling_frequencies, label=f'Number {number}', 
                   color=color, linewidth=2, marker='o', markersize=3)
        
        # Customize chart
        ax.set_xlabel('Date')
        ax.set_ylabel('Rolling Frequency (%)')
        ax.set_title(f'Number Frequency Trends (Rolling {window_size}-draw window)', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        return fig
    
    def create_pattern_visualization(self, pattern_summary: Dict) -> plt.Figure:
        """
        Create visualizations for pattern analysis results.
        
        Args:
            pattern_summary: Pattern analysis results from PatternAnalyzer
            
        Returns:
            matplotlib Figure object with multiple subplots
        """
        self.logger.info("Creating pattern visualization")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(CHART_WIDTH*1.5, CHART_HEIGHT*1.2))
        
        # 1. Consecutive Patterns Chart
        consecutive_patterns = pattern_summary.get('consecutive_patterns', [])
        if consecutive_patterns:
            lengths = [int(p.description.split()[0]) for p in consecutive_patterns]
            frequencies = [p.frequency for p in consecutive_patterns]
            
            bars1 = ax1.bar(lengths, frequencies, color=COLOR_HOT, alpha=0.7)
            ax1.set_xlabel('Consecutive Length')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Consecutive Number Patterns')
            ax1.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, freq in zip(bars1, frequencies):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{freq}', ha='center', va='bottom')
        else:
            ax1.text(0.5, 0.5, 'No consecutive patterns found', 
                    ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Consecutive Number Patterns')
        
        # 2. Odd/Even Distribution
        odd_even_analysis = pattern_summary.get('odd_even_analysis', {})
        if odd_even_analysis and 'pattern_percentages' in odd_even_analysis:
            patterns = list(odd_even_analysis['pattern_percentages'].keys())
            percentages = list(odd_even_analysis['pattern_percentages'].values())
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(patterns)))
            wedges, texts, autotexts = ax2.pie(percentages, labels=patterns, autopct='%1.1f%%',
                                              colors=colors, startangle=90)
            ax2.set_title('Odd/Even Distribution Patterns')
        else:
            ax2.text(0.5, 0.5, 'No odd/even data available', 
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Odd/Even Distribution Patterns')
        
        # 3. Range Distribution
        range_analysis = pattern_summary.get('range_analysis', {})
        if range_analysis and 'percentages' in range_analysis:
            range_names = list(range_analysis['percentages'].keys())
            range_percentages = list(range_analysis['percentages'].values())
            
            # Create nice labels
            range_labels = [name.replace('_', ' ').title() for name in range_names]
            
            bars3 = ax3.bar(range_labels, range_percentages, color=COLOR_NEUTRAL, alpha=0.7)
            ax3.set_xlabel('Number Ranges')
            ax3.set_ylabel('Percentage (%)')
            ax3.set_title('Range Distribution')
            ax3.grid(True, alpha=0.3)
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            
            # Add value labels
            for bar, pct in zip(bars3, range_percentages):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{pct:.1f}%', ha='center', va='bottom')
        else:
            ax3.text(0.5, 0.5, 'No range data available', 
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Range Distribution')
        
        # 4. Sum Distribution
        sum_analysis = pattern_summary.get('sum_analysis', {})
        if sum_analysis and 'sum_distribution' in sum_analysis:
            sum_dist = sum_analysis['sum_distribution']
            sums = list(sum_dist.keys())
            counts = list(sum_dist.values())
            
            # Create histogram-like visualization
            ax4.hist(sums, weights=counts, bins=20, color=COLOR_COLD, alpha=0.7, edgecolor='black')
            ax4.set_xlabel('Sum of Numbers')
            ax4.set_ylabel('Frequency')
            ax4.set_title('Sum Distribution')
            ax4.grid(True, alpha=0.3)
            
            # Add statistics
            avg_sum = sum_analysis.get('average_sum', 0)
            ax4.axvline(avg_sum, color='red', linestyle='--', linewidth=2, label=f'Average: {avg_sum:.1f}')
            ax4.legend()
        else:
            ax4.text(0.5, 0.5, 'No sum data available', 
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Sum Distribution')
        
        plt.tight_layout()
        return fig
    
    def create_recommendation_comparison_chart(self, recommendations: Dict[str, List[int]], 
                                             frequency_data: Dict[int, int]) -> plt.Figure:
        """
        Create a chart comparing different recommendation strategies.
        
        Args:
            recommendations: Dictionary mapping strategy names to number lists
            frequency_data: Historical frequency data for context
            
        Returns:
            matplotlib Figure object
        """
        self.logger.info("Creating recommendation comparison chart")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(CHART_WIDTH*1.5, CHART_HEIGHT))
        
        # 1. Strategy Comparison Bar Chart
        strategy_names = list(recommendations.keys())
        strategy_colors = [COLOR_HOT, COLOR_COLD, COLOR_NEUTRAL][:len(strategy_names)]
        
        # Calculate average frequency for each strategy
        avg_frequencies = []
        for strategy, numbers in recommendations.items():
            avg_freq = sum(frequency_data.get(num, 0) for num in numbers) / len(numbers)
            avg_frequencies.append(avg_freq)
        
        bars = ax1.bar(strategy_names, avg_frequencies, color=strategy_colors, alpha=0.7)
        ax1.set_ylabel('Average Frequency')
        ax1.set_title('Strategy Frequency Comparison')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, freq in zip(bars, avg_frequencies):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{freq:.1f}', ha='center', va='bottom')
        
        # Rotate x-axis labels if needed
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 2. Number Distribution Heatmap
        all_numbers = set()
        for numbers in recommendations.values():
            all_numbers.update(numbers)
        
        all_numbers = sorted(list(all_numbers))
        
        # Create matrix for heatmap
        matrix = []
        for strategy in strategy_names:
            row = [1 if num in recommendations[strategy] else 0 for num in all_numbers]
            matrix.append(row)
        
        im = ax2.imshow(matrix, cmap='RdYlBu_r', aspect='auto')
        
        # Set ticks and labels
        ax2.set_xticks(range(len(all_numbers)))
        ax2.set_xticklabels(all_numbers)
        ax2.set_yticks(range(len(strategy_names)))
        ax2.set_yticklabels(strategy_names)
        
        ax2.set_xlabel('Numbers')
        ax2.set_title('Strategy Number Selection')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label('Selected')
        
        plt.tight_layout()
        return fig
    
    def save_chart(self, fig: plt.Figure, filename: str, format: str = 'png') -> str:
        """
        Save a chart to file.
        
        Args:
            fig: matplotlib Figure object
            filename: Output filename (without extension)
            format: File format ('png', 'pdf', 'svg')
            
        Returns:
            Full path to saved file
        """
        full_filename = f"{filename}.{format}"
        
        try:
            fig.savefig(full_filename, format=format, dpi=CHART_DPI, 
                       bbox_inches='tight', facecolor='white')
            self.logger.info(f"Chart saved to {full_filename}")
            return full_filename
        except Exception as e:
            self.logger.error(f"Failed to save chart: {e}")
            raise
    
    def create_comprehensive_dashboard(self, draws: List[DrawResult], 
                                    frequency_data: Dict[int, int],
                                    pattern_summary: Dict,
                                    recommendations: Dict[str, List[int]]) -> plt.Figure:
        """
        Create a comprehensive dashboard with multiple visualizations.
        
        Args:
            draws: Historical draw data
            frequency_data: Number frequency data
            pattern_summary: Pattern analysis results
            recommendations: Strategy recommendations
            
        Returns:
            matplotlib Figure object with dashboard layout
        """
        self.logger.info("Creating comprehensive dashboard")
        
        fig = plt.figure(figsize=(CHART_WIDTH*2, CHART_HEIGHT*2))
        
        # Create grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Frequency chart (top row, spans 2 columns)
        ax1 = fig.add_subplot(gs[0, :2])
        numbers = list(range(1, 51))
        frequencies = [frequency_data.get(num, 0) for num in numbers]
        bars = ax1.bar(numbers, frequencies, color=COLOR_NEUTRAL, alpha=0.7)
        ax1.set_title('Number Frequency Distribution')
        ax1.set_xlabel('Numbers')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        
        # 2. Odd/Even pie chart (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        odd_even = pattern_summary.get('odd_even_analysis', {})
        if odd_even and 'pattern_percentages' in odd_even:
            patterns = list(odd_even['pattern_percentages'].keys())[:4]  # Top 4 patterns
            percentages = [odd_even['pattern_percentages'][p] for p in patterns]
            ax2.pie(percentages, labels=patterns, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Odd/Even Patterns')
        
        # 3. Range distribution (middle left)
        ax3 = fig.add_subplot(gs[1, 0])
        range_analysis = pattern_summary.get('range_analysis', {})
        if range_analysis and 'percentages' in range_analysis:
            ranges = list(range_analysis['percentages'].keys())
            percentages = list(range_analysis['percentages'].values())
            ax3.bar(range(len(ranges)), percentages, color=COLOR_COLD, alpha=0.7)
            ax3.set_xticks(range(len(ranges)))
            ax3.set_xticklabels([r.replace('_', '\n') for r in ranges], fontsize=8)
        ax3.set_title('Range Distribution')
        ax3.set_ylabel('Percentage')
        
        # 4. Consecutive patterns (middle center)
        ax4 = fig.add_subplot(gs[1, 1])
        consecutive = pattern_summary.get('consecutive_patterns', [])
        if consecutive:
            lengths = [int(p.description.split()[0]) for p in consecutive]
            freqs = [p.frequency for p in consecutive]
            ax4.bar(lengths, freqs, color=COLOR_HOT, alpha=0.7)
            ax4.set_xlabel('Length')
            ax4.set_ylabel('Count')
        ax4.set_title('Consecutive Patterns')
        
        # 5. Recommendation comparison (middle right)
        ax5 = fig.add_subplot(gs[1, 2])
        if recommendations:
            strategies = list(recommendations.keys())
            avg_freqs = []
            for strategy, numbers in recommendations.items():
                avg_freq = sum(frequency_data.get(num, 0) for num in numbers) / len(numbers)
                avg_freqs.append(avg_freq)
            
            ax5.bar(strategies, avg_freqs, color=[COLOR_HOT, COLOR_COLD, COLOR_NEUTRAL][:len(strategies)], alpha=0.7)
            ax5.set_ylabel('Avg Frequency')
            plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, fontsize=8)
        ax5.set_title('Strategy Comparison')
        
        # 6. Summary statistics (bottom row)
        ax6 = fig.add_subplot(gs[2, :])
        ax6.axis('off')
        
        # Create summary text
        total_draws = len(draws)
        avg_frequency = np.mean(list(frequency_data.values()))
        pattern_score = pattern_summary.get('pattern_score', 0)
        
        summary_text = f"""
        LOTTO MAX ANALYSIS SUMMARY
        
        Total Draws Analyzed: {total_draws}
        Date Range: {draws[0].date.strftime('%Y-%m-%d')} to {draws[-1].date.strftime('%Y-%m-%d')}
        Average Number Frequency: {avg_frequency:.1f}
        Pattern Complexity Score: {pattern_score:.1f}/100
        
        Most Frequent Numbers: {sorted(frequency_data.items(), key=lambda x: x[1], reverse=True)[:5]}
        Least Frequent Numbers: {sorted(frequency_data.items(), key=lambda x: x[1])[:5]}
        """
        
        ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.suptitle('Lotto Max Analysis Dashboard', fontsize=16, fontweight='bold')
        
        return fig