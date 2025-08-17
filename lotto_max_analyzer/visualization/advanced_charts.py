"""
Advanced visualization module for Lotto Max Analyzer.
Creates sophisticated charts and pattern analysis visualizations.
"""

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from ..data.models import DrawResult, FrequencyStats, Pattern
from ..analysis.recommendations import Recommendation


class AdvancedChartGenerator:
    """Advanced chart generator with sophisticated visualizations."""
    
    def __init__(self):
        """Initialize the advanced chart generator."""
        self.logger = logging.getLogger(__name__)
        
        # Set style for better-looking charts
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('default')
        
        if HAS_SEABORN:
            sns.set_palette("husl")
    
    def create_correlation_heatmap(self, draws: List[DrawResult], 
                                 save_path: Optional[Path] = None) -> Path:
        """Create a correlation heatmap showing number co-occurrence patterns."""
        if save_path is None:
            save_path = Path("lotto_max_correlation_heatmap.png")
        
        self.logger.info("Creating correlation heatmap")
        
        # Create co-occurrence matrix
        matrix = np.zeros((50, 50))
        
        for draw in draws:
            for i, num1 in enumerate(draw.numbers):
                for j, num2 in enumerate(draw.numbers):
                    if i != j:
                        matrix[num1-1][num2-1] += 1
        
        # Normalize the matrix
        matrix = matrix / len(draws)
        
        # Create the heatmap
        plt.figure(figsize=(14, 12))
        
        if HAS_SEABORN:
            sns.heatmap(matrix, 
                       xticklabels=range(1, 51), 
                       yticklabels=range(1, 51),
                       cmap='YlOrRd', 
                       cbar_kws={'label': 'Co-occurrence Probability'})
        else:
            # Fallback to matplotlib imshow
            plt.imshow(matrix, cmap='YlOrRd', aspect='equal')
            plt.colorbar(label='Co-occurrence Probability')
            plt.xticks(range(0, 50, 5), range(1, 51, 5))
            plt.yticks(range(0, 50, 5), range(1, 51, 5))
        
        plt.title('🔥 Number Co-occurrence Correlation Heatmap', fontsize=16, fontweight='bold')
        plt.xlabel('Numbers', fontsize=12)
        plt.ylabel('Numbers', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Correlation heatmap saved to {save_path}")
        return save_path
    
    def create_advanced_pattern_analysis(self, draws: List[DrawResult], 
                                       save_path: Optional[Path] = None) -> Path:
        """Create comprehensive pattern analysis visualization."""
        if save_path is None:
            save_path = Path("lotto_max_advanced_patterns.png")
        
        self.logger.info("Creating advanced pattern analysis")
        
        fig, axes = plt.subplots(2, 3, figsize=(20, 14))
        fig.suptitle('🔍 ADVANCED PATTERN ANALYSIS', fontsize=18, fontweight='bold')
        
        # 1. Sum distribution with statistical analysis
        ax1 = axes[0, 0]
        sums = [sum(draw.numbers) for draw in draws]
        
        ax1.hist(sums, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(sums), color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {np.mean(sums):.1f}')
        ax1.axvline(np.median(sums), color='green', linestyle='--', linewidth=2, 
                   label=f'Median: {np.median(sums):.1f}')
        ax1.set_title('Sum Distribution Analysis', fontweight='bold')
        ax1.set_xlabel('Sum of 7 Numbers')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Gap analysis between consecutive numbers
        ax2 = axes[0, 1]
        gaps = []
        for draw in draws:
            sorted_nums = sorted(draw.numbers)
            draw_gaps = [sorted_nums[i+1] - sorted_nums[i] for i in range(len(sorted_nums)-1)]
            gaps.extend(draw_gaps)
        
        ax2.hist(gaps, bins=range(1, 21), alpha=0.7, color='orange', edgecolor='black')
        ax2.set_title('Gap Analysis Between Numbers', fontweight='bold')
        ax2.set_xlabel('Gap Size')
        ax2.set_ylabel('Frequency')
        ax2.grid(True, alpha=0.3)
        
        # 3. Odd/Even distribution patterns
        ax3 = axes[0, 2]
        odd_even_patterns = {}
        for draw in draws:
            odd_count = sum(1 for num in draw.numbers if num % 2 == 1)
            even_count = 7 - odd_count
            pattern = f"{odd_count}-{even_count}"
            odd_even_patterns[pattern] = odd_even_patterns.get(pattern, 0) + 1
        
        patterns = list(odd_even_patterns.keys())
        counts = list(odd_even_patterns.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(patterns)))
        
        wedges, texts, autotexts = ax3.pie(counts, labels=patterns, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax3.set_title('Odd/Even Distribution Patterns', fontweight='bold')
        
        # 4. Range distribution (1-10, 11-20, etc.)
        ax4 = axes[1, 0]
        range_counts = {f"{i*10+1}-{(i+1)*10}": 0 for i in range(5)}
        
        for draw in draws:
            for num in draw.numbers:
                range_key = f"{((num-1)//10)*10+1}-{((num-1)//10+1)*10}"
                if range_key in range_counts:
                    range_counts[range_key] += 1
        
        ranges = list(range_counts.keys())
        range_values = list(range_counts.values())
        
        bars = ax4.bar(ranges, range_values, color='purple', alpha=0.7)
        ax4.set_title('Number Range Distribution', fontweight='bold')
        ax4.set_xlabel('Number Ranges')
        ax4.set_ylabel('Total Occurrences')
        ax4.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, range_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 5,
                    f'{value}', ha='center', va='bottom')
        
        # 5. Consecutive number analysis
        ax5 = axes[1, 1]
        consecutive_counts = {i: 0 for i in range(2, 8)}
        
        for draw in draws:
            sorted_nums = sorted(draw.numbers)
            consecutive_sequences = []
            current_seq = [sorted_nums[0]]
            
            for i in range(1, len(sorted_nums)):
                if sorted_nums[i] == sorted_nums[i-1] + 1:
                    current_seq.append(sorted_nums[i])
                else:
                    if len(current_seq) >= 2:
                        consecutive_sequences.append(len(current_seq))
                    current_seq = [sorted_nums[i]]
            
            if len(current_seq) >= 2:
                consecutive_sequences.append(len(current_seq))
            
            for seq_len in consecutive_sequences:
                if seq_len in consecutive_counts:
                    consecutive_counts[seq_len] += 1
        
        seq_lengths = list(consecutive_counts.keys())
        seq_counts = list(consecutive_counts.values())
        
        ax5.bar(seq_lengths, seq_counts, color='red', alpha=0.7)
        ax5.set_title('Consecutive Number Patterns', fontweight='bold')
        ax5.set_xlabel('Consecutive Sequence Length')
        ax5.set_ylabel('Occurrences')
        ax5.grid(True, alpha=0.3)
        
        # 6. Prime vs Composite number analysis
        ax6 = axes[1, 2]
        
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    return False
            return True
        
        prime_counts = []
        composite_counts = []
        
        for draw in draws:
            prime_count = sum(1 for num in draw.numbers if is_prime(num))
            composite_count = 7 - prime_count
            prime_counts.append(prime_count)
            composite_counts.append(composite_count)
        
        x = np.arange(len(draws))
        width = 0.35
        
        # Show distribution of prime vs composite
        prime_dist = {}
        for count in prime_counts:
            prime_dist[count] = prime_dist.get(count, 0) + 1
        
        prime_keys = list(prime_dist.keys())
        prime_values = list(prime_dist.values())
        
        ax6.bar(prime_keys, prime_values, color='gold', alpha=0.7)
        ax6.set_title('Prime Numbers per Draw Distribution', fontweight='bold')
        ax6.set_xlabel('Number of Prime Numbers')
        ax6.set_ylabel('Frequency')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Advanced pattern analysis saved to {save_path}")
        return save_path
    
    def create_time_series_analysis(self, draws: List[DrawResult], 
                                  save_path: Optional[Path] = None) -> Path:
        """Create comprehensive time series analysis."""
        if save_path is None:
            save_path = Path("lotto_max_time_series.png")
        
        self.logger.info("Creating time series analysis")
        
        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.suptitle('📈 TIME SERIES ANALYSIS', fontsize=18, fontweight='bold')
        
        # Sort draws by date
        sorted_draws = sorted(draws, key=lambda d: d.date)
        dates = [draw.date for draw in sorted_draws]
        
        # 1. Jackpot progression with trend analysis
        ax1 = axes[0, 0]
        jackpots = [draw.jackpot_amount for draw in sorted_draws]
        
        ax1.plot(dates, jackpots, color='gold', linewidth=2, alpha=0.8)
        ax1.fill_between(dates, jackpots, alpha=0.3, color='gold')
        
        # Add trend line
        x_numeric = np.arange(len(jackpots))
        z = np.polyfit(x_numeric, jackpots, 1)
        p = np.poly1d(z)
        ax1.plot(dates, p(x_numeric), "r--", alpha=0.8, linewidth=2, label='Trend')
        
        ax1.set_title('Jackpot Progression Over Time', fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Jackpot Amount ($)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Moving average of sum values
        ax2 = axes[0, 1]
        sums = [sum(draw.numbers) for draw in sorted_draws]
        
        # Calculate moving average
        window_size = min(20, len(sums) // 10)
        if window_size > 1:
            moving_avg = np.convolve(sums, np.ones(window_size)/window_size, mode='valid')
            moving_dates = dates[window_size-1:]
            
            ax2.plot(dates, sums, alpha=0.3, color='blue', label='Raw Data')
            ax2.plot(moving_dates, moving_avg, color='red', linewidth=2, 
                    label=f'{window_size}-Draw Moving Average')
        else:
            ax2.plot(dates, sums, color='blue', linewidth=2)
        
        ax2.set_title('Sum Trends with Moving Average', fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Sum of Numbers')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Seasonal patterns (monthly analysis)
        ax3 = axes[1, 0]
        monthly_data = {}
        
        for draw in sorted_draws:
            month = draw.date.strftime('%B')
            if month not in monthly_data:
                monthly_data[month] = []
            monthly_data[month].append(sum(draw.numbers))
        
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        
        monthly_avgs = []
        for month in months:
            if month in monthly_data:
                monthly_avgs.append(np.mean(monthly_data[month]))
            else:
                monthly_avgs.append(0)
        
        bars = ax3.bar(range(12), monthly_avgs, color='green', alpha=0.7)
        ax3.set_title('Seasonal Patterns (Monthly Averages)', fontweight='bold')
        ax3.set_xlabel('Month')
        ax3.set_ylabel('Average Sum')
        ax3.set_xticks(range(12))
        ax3.set_xticklabels([m[:3] for m in months], rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, avg) in enumerate(zip(bars, monthly_avgs)):
            if avg > 0:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{avg:.1f}', ha='center', va='bottom')
        
        # 4. Volatility analysis
        ax4 = axes[1, 1]
        
        # Calculate rolling standard deviation
        window_size = min(30, len(sums) // 5)
        if window_size > 1:
            rolling_std = []
            for i in range(window_size, len(sums)):
                window_data = sums[i-window_size:i]
                rolling_std.append(np.std(window_data))
            
            volatility_dates = dates[window_size:]
            ax4.plot(volatility_dates, rolling_std, color='purple', linewidth=2)
            ax4.fill_between(volatility_dates, rolling_std, alpha=0.3, color='purple')
        
        ax4.set_title('Sum Volatility Analysis', fontweight='bold')
        ax4.set_xlabel('Date')
        ax4.set_ylabel('Rolling Standard Deviation')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Time series analysis saved to {save_path}")
        return save_path
    
    def create_statistical_distribution_analysis(self, draws: List[DrawResult], 
                                               save_path: Optional[Path] = None) -> Path:
        """Create statistical distribution analysis."""
        if save_path is None:
            save_path = Path("lotto_max_statistical_distributions.png")
        
        self.logger.info("Creating statistical distribution analysis")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('📊 STATISTICAL DISTRIBUTION ANALYSIS', fontsize=18, fontweight='bold')
        
        # 1. Number frequency distribution with normal overlay
        ax1 = axes[0, 0]
        all_numbers = []
        for draw in draws:
            all_numbers.extend(draw.numbers)
        
        ax1.hist(all_numbers, bins=range(1, 52), alpha=0.7, color='skyblue', 
                density=True, edgecolor='black')
        
        # Overlay normal distribution
        mu, sigma = np.mean(all_numbers), np.std(all_numbers)
        x = np.linspace(1, 50, 100)
        normal_dist = (1/(sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        ax1.plot(x, normal_dist, 'r-', linewidth=2, label=f'Normal (μ={mu:.1f}, σ={sigma:.1f})')
        
        ax1.set_title('Number Frequency Distribution', fontweight='bold')
        ax1.set_xlabel('Numbers')
        ax1.set_ylabel('Density')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Q-Q plot for normality test
        ax2 = axes[0, 1]
        
        sums = [sum(draw.numbers) for draw in draws]
        
        if HAS_SCIPY:
            stats.probplot(sums, dist="norm", plot=ax2)
            ax2.set_title('Q-Q Plot: Sum Normality Test', fontweight='bold')
        else:
            # Fallback: simple histogram
            ax2.hist(sums, bins=20, alpha=0.7, color='orange')
            ax2.set_title('Sum Distribution (scipy not available)', fontweight='bold')
            ax2.set_xlabel('Sum Values')
            ax2.set_ylabel('Frequency')
        
        ax2.grid(True, alpha=0.3)
        
        # 3. Box plot of numbers by position
        ax3 = axes[1, 0]
        position_data = [[] for _ in range(7)]
        
        for draw in draws:
            sorted_nums = sorted(draw.numbers)
            for i, num in enumerate(sorted_nums):
                position_data[i].append(num)
        
        ax3.boxplot(position_data, labels=[f'Pos {i+1}' for i in range(7)])
        ax3.set_title('Number Distribution by Position', fontweight='bold')
        ax3.set_xlabel('Position (Sorted)')
        ax3.set_ylabel('Number Value')
        ax3.grid(True, alpha=0.3)
        
        # 4. Cumulative distribution function
        ax4 = axes[1, 1]
        
        # Calculate empirical CDF for sums
        sorted_sums = np.sort(sums)
        y = np.arange(1, len(sorted_sums) + 1) / len(sorted_sums)
        
        ax4.plot(sorted_sums, y, 'b-', linewidth=2, label='Empirical CDF')
        
        # Overlay theoretical normal CDF if scipy available
        if HAS_SCIPY:
            theoretical_cdf = stats.norm.cdf(sorted_sums, mu, sigma)
            ax4.plot(sorted_sums, theoretical_cdf, 'r--', linewidth=2, label='Normal CDF')
        
        ax4.set_title('Cumulative Distribution Function', fontweight='bold')
        ax4.set_xlabel('Sum Values')
        ax4.set_ylabel('Cumulative Probability')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Statistical distribution analysis saved to {save_path}")
        return save_path    
    
    def create_statistical_distribution_analysis_v2(self, draws: List[DrawResult], 
                                                   save_path: Optional[Path] = None) -> Path:
        """Create comprehensive statistical distribution analysis."""
        if save_path is None:
            save_path = Path("lotto_max_statistical_distributions.png")
        
        self.logger.info("Creating statistical distribution analysis")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('📊 STATISTICAL DISTRIBUTION ANALYSIS', fontsize=18, fontweight='bold')
        
        # 1. Number frequency distribution with statistical tests
        ax1 = axes[0, 0]
        all_numbers = []
        for draw in draws:
            all_numbers.extend(draw.numbers)
        
        # Create histogram
        counts, bins, patches = ax1.hist(all_numbers, bins=range(1, 52), alpha=0.7, 
                                        color='skyblue', edgecolor='black', density=True)
        
        # Overlay theoretical uniform distribution
        uniform_prob = 1/50
        ax1.axhline(y=uniform_prob, color='red', linestyle='--', linewidth=2, 
                   label=f'Uniform Distribution ({uniform_prob:.3f})')
        
        ax1.set_title('Number Frequency vs Uniform Distribution', fontweight='bold')
        ax1.set_xlabel('Numbers')
        ax1.set_ylabel('Probability Density')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Chi-square goodness of fit test visualization
        ax2 = axes[0, 1]
        
        # Calculate observed vs expected frequencies
        observed_freq = [0] * 50
        for num in all_numbers:
            observed_freq[num-1] += 1
        
        expected_freq = len(all_numbers) / 50
        expected_freqs = [expected_freq] * 50
        
        # Perform chi-square test if scipy available
        if HAS_SCIPY:
            chi2_stat, p_value = stats.chisquare(observed_freq, expected_freqs)
        else:
            chi2_stat, p_value = 0, 1  # Fallback values
        
        x_pos = np.arange(1, 51)
        width = 0.35
        
        bars1 = ax2.bar(x_pos - width/2, observed_freq, width, label='Observed', 
                       color='blue', alpha=0.7)
        bars2 = ax2.bar(x_pos + width/2, expected_freqs, width, label='Expected', 
                       color='red', alpha=0.7)
        
        ax2.set_title(f'Chi-Square Test (χ²={chi2_stat:.2f}, p={p_value:.4f})', fontweight='bold')
        ax2.set_xlabel('Numbers')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Sum distribution with normal fit
        ax3 = axes[1, 0]
        sums = [sum(draw.numbers) for draw in draws]
        
        # Create histogram
        n, bins, patches = ax3.hist(sums, bins=30, alpha=0.7, color='green', 
                                   density=True, edgecolor='black')
        
        # Fit normal distribution if scipy available
        if HAS_SCIPY:
            mu, sigma = stats.norm.fit(sums)
            x = np.linspace(min(sums), max(sums), 100)
            normal_fit = stats.norm.pdf(x, mu, sigma)
            ax3.plot(x, normal_fit, 'r-', linewidth=2, 
                    label=f'Normal Fit (μ={mu:.1f}, σ={sigma:.1f})')
            
            # Add statistical info
            skewness = stats.skew(sums)
            kurtosis = stats.kurtosis(sums)
        else:
            # Fallback: basic statistics
            mu = np.mean(sums)
            sigma = np.std(sums)
            skewness = 0
            kurtosis = 0
        
        ax3.set_title(f'Sum Distribution (Skew={skewness:.2f}, Kurt={kurtosis:.2f})', 
                     fontweight='bold')
        ax3.set_xlabel('Sum of Numbers')
        ax3.set_ylabel('Density')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Autocorrelation analysis
        ax4 = axes[1, 1]
        
        # Calculate autocorrelation of sums
        max_lag = min(50, len(sums) // 4)
        lags = range(max_lag)
        autocorr = [np.corrcoef(sums[:-lag or None], sums[lag:])[0, 1] if lag > 0 
                   else 1.0 for lag in lags]
        
        ax4.plot(lags, autocorr, 'b-', linewidth=2, marker='o', markersize=4)
        ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax4.axhline(y=0.05, color='orange', linestyle='--', alpha=0.5, label='5% threshold')
        ax4.axhline(y=-0.05, color='orange', linestyle='--', alpha=0.5)
        
        ax4.set_title('Autocorrelation Analysis', fontweight='bold')
        ax4.set_xlabel('Lag')
        ax4.set_ylabel('Autocorrelation')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Statistical distribution analysis saved to {save_path}")
        return save_path
    
    def create_prediction_confidence_analysis(self, recommendations: Dict[str, Recommendation],
                                            save_path: Optional[Path] = None) -> Path:
        """Create visualization comparing prediction confidence across strategies."""
        if save_path is None:
            save_path = Path("lotto_max_prediction_confidence.png")
        
        self.logger.info("Creating prediction confidence analysis")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('🎯 PREDICTION CONFIDENCE ANALYSIS', fontsize=18, fontweight='bold')
        
        strategies = list(recommendations.keys())
        confidences = [rec.confidence for rec in recommendations.values()]
        colors = ['red', 'blue', 'green', 'purple', 'orange'][:len(strategies)]
        
        # 1. Confidence comparison bar chart
        ax1 = axes[0, 0]
        bars = ax1.bar(strategies, confidences, color=colors, alpha=0.7)
        ax1.set_title('Strategy Confidence Comparison', fontweight='bold')
        ax1.set_ylabel('Confidence Score')
        ax1.set_ylim(0, 1)
        ax1.tick_params(axis='x', rotation=45)
        
        # Add confidence values on bars
        for bar, conf in zip(bars, confidences):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{conf:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Confidence radar chart
        ax2 = axes[0, 1]
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(strategies), endpoint=False).tolist()
        confidences_radar = confidences + [confidences[0]]  # Close the circle
        angles += angles[:1]
        
        ax2 = plt.subplot(2, 2, 2, projection='polar')
        ax2.plot(angles, confidences_radar, 'o-', linewidth=2, color='blue')
        ax2.fill(angles, confidences_radar, alpha=0.25, color='blue')
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(strategies)
        ax2.set_ylim(0, 1)
        ax2.set_title('Confidence Radar Chart', fontweight='bold', pad=20)
        
        # 3. Number overlap analysis
        ax3 = axes[1, 0]
        
        # Calculate overlap between strategies
        overlap_matrix = np.zeros((len(strategies), len(strategies)))
        
        for i, strategy1 in enumerate(strategies):
            for j, strategy2 in enumerate(strategies):
                if i != j:
                    set1 = set(recommendations[strategy1].numbers)
                    set2 = set(recommendations[strategy2].numbers)
                    overlap = len(set1.intersection(set2))
                    overlap_matrix[i][j] = overlap
        
        im = ax3.imshow(overlap_matrix, cmap='YlOrRd', aspect='auto')
        ax3.set_title('Strategy Number Overlap', fontweight='bold')
        ax3.set_xticks(range(len(strategies)))
        ax3.set_yticks(range(len(strategies)))
        ax3.set_xticklabels(strategies, rotation=45)
        ax3.set_yticklabels(strategies)
        
        # Add overlap values to cells
        for i in range(len(strategies)):
            for j in range(len(strategies)):
                if i != j:
                    ax3.text(j, i, f'{int(overlap_matrix[i][j])}', 
                            ha='center', va='center', fontweight='bold')
        
        plt.colorbar(im, ax=ax3, label='Number of Overlapping Numbers')
        
        # 4. Strategy characteristics
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Create strategy summary
        summary_text = "STRATEGY CHARACTERISTICS\n" + "="*40 + "\n\n"
        
        for strategy, rec in recommendations.items():
            strategy_name = strategy.replace('_', ' ').title()
            summary_text += f"🎯 {strategy_name}:\n"
            summary_text += f"   Numbers: {rec.numbers}\n"
            summary_text += f"   Confidence: {rec.confidence:.3f}\n"
            
            # Calculate additional metrics
            odd_count = sum(1 for n in rec.numbers if n % 2 == 1)
            sum_total = sum(rec.numbers)
            
            summary_text += f"   Odd/Even: {odd_count}-{7-odd_count}\n"
            summary_text += f"   Sum: {sum_total}\n"
            summary_text += f"   Range: {min(rec.numbers)}-{max(rec.numbers)}\n\n"
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Prediction confidence analysis saved to {save_path}")
        return save_path