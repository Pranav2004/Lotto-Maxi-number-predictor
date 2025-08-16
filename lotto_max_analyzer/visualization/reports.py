"""Report generation module for Lotto Max analysis."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from statistics import mean, stdev
import textwrap

from ..data.models import DrawResult, Recommendation
from ..config import NUMBER_RANGES


class ReportGenerator:
    """Generates text-based reports for Lotto Max analysis."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_frequency_report(self, draws: List[DrawResult], 
                                frequency_data: Dict[int, int],
                                hot_numbers: List[int],
                                cold_numbers: List[int]) -> str:
        """
        Generate a comprehensive frequency analysis report.
        
        Args:
            draws: List of DrawResult objects
            frequency_data: Number frequency data
            hot_numbers: List of hot numbers
            cold_numbers: List of cold numbers
            
        Returns:
            Formatted text report
        """
        self.logger.info("Generating frequency report")
        
        if not draws:
            return "No data available for frequency report."
        
        # Calculate statistics
        total_draws = len(draws)
        date_range = f"{draws[0].date.strftime('%Y-%m-%d')} to {draws[-1].date.strftime('%Y-%m-%d')}"
        frequencies = list(frequency_data.values())
        avg_frequency = mean(frequencies)
        std_frequency = stdev(frequencies) if len(frequencies) > 1 else 0
        min_frequency = min(frequencies)
        max_frequency = max(frequencies)
        
        # Sort numbers by frequency
        sorted_by_freq = sorted(frequency_data.items(), key=lambda x: x[1], reverse=True)
        
        report = []
        report.append("=" * 80)
        report.append("LOTTO MAX FREQUENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary section
        report.append("ANALYSIS SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Draws Analyzed: {total_draws}")
        report.append(f"Analysis Period: {date_range}")
        report.append(f"Total Numbers Drawn: {sum(frequencies)} (7 per draw)")
        report.append(f"Expected Frequency per Number: {avg_frequency:.1f}")
        report.append(f"Frequency Standard Deviation: {std_frequency:.1f}")
        report.append(f"Frequency Range: {min_frequency} - {max_frequency}")
        report.append("")
        
        # Hot numbers section
        report.append("HOT NUMBERS (High Frequency)")
        report.append("-" * 40)
        if hot_numbers:
            report.append(f"Numbers appearing more frequently than expected:")
            for i, num in enumerate(hot_numbers[:10], 1):
                freq = frequency_data[num]
                percentage = (freq / sum(frequencies)) * 100
                deviation = ((freq / avg_frequency) - 1) * 100
                report.append(f"{i:2d}. Number {num:2d}: {freq:3d} times ({percentage:4.1f}%, +{deviation:4.1f}%)")
        else:
            report.append("No hot numbers identified with current thresholds.")
        report.append("")
        
        # Cold numbers section
        report.append("COLD NUMBERS (Low Frequency)")
        report.append("-" * 40)
        if cold_numbers:
            report.append(f"Numbers appearing less frequently than expected:")
            for i, num in enumerate(cold_numbers[:10], 1):
                freq = frequency_data[num]
                percentage = (freq / sum(frequencies)) * 100
                deviation = ((freq / avg_frequency) - 1) * 100
                report.append(f"{i:2d}. Number {num:2d}: {freq:3d} times ({percentage:4.1f}%, {deviation:4.1f}%)")
        else:
            report.append("No cold numbers identified with current thresholds.")
        report.append("")
        
        # Top and bottom performers
        report.append("FREQUENCY RANKINGS")
        report.append("-" * 40)
        report.append("Most Frequent Numbers:")
        for i, (num, freq) in enumerate(sorted_by_freq[:10], 1):
            percentage = (freq / sum(frequencies)) * 100
            report.append(f"{i:2d}. Number {num:2d}: {freq:3d} times ({percentage:4.1f}%)")
        
        report.append("")
        report.append("Least Frequent Numbers:")
        for i, (num, freq) in enumerate(sorted_by_freq[-10:], 1):
            percentage = (freq / sum(frequencies)) * 100
            report.append(f"{i:2d}. Number {num:2d}: {freq:3d} times ({percentage:4.1f}%)")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_pattern_report(self, pattern_summary: Dict) -> str:
        """
        Generate a comprehensive pattern analysis report.
        
        Args:
            pattern_summary: Pattern analysis results
            
        Returns:
            Formatted text report
        """
        self.logger.info("Generating pattern report")
        
        report = []
        report.append("=" * 80)
        report.append("LOTTO MAX PATTERN ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_draws = pattern_summary.get('total_draws', 0)
        pattern_score = pattern_summary.get('pattern_score', 0)
        
        # Summary
        report.append("PATTERN SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Draws Analyzed: {total_draws}")
        report.append(f"Overall Pattern Complexity Score: {pattern_score:.1f}/100")
        report.append("")
        
        # Consecutive patterns
        consecutive_patterns = pattern_summary.get('consecutive_patterns', [])
        report.append("CONSECUTIVE NUMBER PATTERNS")
        report.append("-" * 40)
        if consecutive_patterns:
            for pattern in consecutive_patterns:
                significance_desc = "High" if pattern.significance > 0.7 else "Medium" if pattern.significance > 0.4 else "Low"
                report.append(f"{pattern.description}: {pattern.frequency} occurrences")
                report.append(f"  Significance: {pattern.significance:.2f} ({significance_desc})")
                if pattern.examples:
                    examples_str = ", ".join([str(ex) for ex in pattern.examples[:3]])
                    report.append(f"  Examples: {examples_str}")
                report.append("")
        else:
            report.append("No significant consecutive patterns detected.")
            report.append("")
        
        # Odd/Even analysis
        odd_even = pattern_summary.get('odd_even_analysis', {})
        report.append("ODD/EVEN DISTRIBUTION ANALYSIS")
        report.append("-" * 40)
        if odd_even:
            avg_odd = odd_even.get('average_odd_count', 0)
            avg_even = odd_even.get('average_even_count', 0)
            most_common = odd_even.get('most_common_pattern', ('Unknown', 0))
            
            report.append(f"Average Odd Numbers per Draw: {avg_odd:.1f}")
            report.append(f"Average Even Numbers per Draw: {avg_even:.1f}")
            report.append(f"Most Common Pattern: {most_common[0]} ({most_common[1]} times)")
            report.append("")
            
            report.append("Pattern Distribution:")
            pattern_percentages = odd_even.get('pattern_percentages', {})
            for pattern, percentage in sorted(pattern_percentages.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {pattern} (odd-even): {percentage:.1f}%")
        else:
            report.append("No odd/even analysis data available.")
        report.append("")
        
        # Range analysis
        range_analysis = pattern_summary.get('range_analysis', {})
        report.append("NUMBER RANGE DISTRIBUTION")
        report.append("-" * 40)
        if range_analysis:
            balance_score = range_analysis.get('range_balance_score', 0)
            report.append(f"Range Balance Score: {balance_score:.1f}/100")
            
            balance_assessment = (
                "Excellent" if balance_score > 80 else
                "Good" if balance_score > 60 else
                "Fair" if balance_score > 40 else
                "Poor"
            )
            report.append(f"Balance Assessment: {balance_assessment}")
            report.append("")
            
            percentages = range_analysis.get('percentages', {})
            avg_per_draw = range_analysis.get('average_per_draw', {})
            
            for range_name in ['low', 'mid_low', 'mid', 'mid_high', 'high']:
                if range_name in percentages:
                    range_label = range_name.replace('_', ' ').title()
                    pct = percentages[range_name]
                    avg = avg_per_draw.get(range_name, 0)
                    range_bounds = NUMBER_RANGES.get(range_name, (0, 0))
                    report.append(f"{range_label} ({range_bounds[0]}-{range_bounds[1]}): {pct:.1f}% ({avg:.1f} avg/draw)")
        else:
            report.append("No range analysis data available.")
        report.append("")
        
        # Sum analysis
        sum_analysis = pattern_summary.get('sum_analysis', {})
        report.append("NUMBER SUM ANALYSIS")
        report.append("-" * 40)
        if sum_analysis:
            avg_sum = sum_analysis.get('average_sum', 0)
            min_sum = sum_analysis.get('min_sum', 0)
            max_sum = sum_analysis.get('max_sum', 0)
            std_sum = sum_analysis.get('std_deviation', 0)
            
            report.append(f"Average Sum: {avg_sum:.1f}")
            report.append(f"Sum Range: {min_sum} - {max_sum}")
            report.append(f"Standard Deviation: {std_sum:.1f}")
            
            # Theoretical range for 7 numbers from 1-50
            theoretical_min = sum(range(1, 8))  # 1+2+3+4+5+6+7 = 28
            theoretical_max = sum(range(44, 51))  # 44+45+46+47+48+49+50 = 329
            theoretical_avg = (theoretical_min + theoretical_max) / 2
            
            report.append(f"Theoretical Average: {theoretical_avg:.1f}")
            deviation = ((avg_sum / theoretical_avg) - 1) * 100
            report.append(f"Deviation from Theoretical: {deviation:+.1f}%")
        else:
            report.append("No sum analysis data available.")
        report.append("")
        
        # Gap analysis
        gap_analysis = pattern_summary.get('gap_analysis', {})
        report.append("NUMBER GAP ANALYSIS")
        report.append("-" * 40)
        if gap_analysis:
            avg_gap = gap_analysis.get('average_gap', 0)
            min_gap = gap_analysis.get('min_gap', 0)
            max_gap = gap_analysis.get('max_gap', 0)
            
            report.append(f"Average Gap Between Numbers: {avg_gap:.1f}")
            report.append(f"Gap Range: {min_gap} - {max_gap}")
            
            # Theoretical average gap
            theoretical_avg_gap = 49 / 6  # (50-1) / (7-1) ≈ 8.17
            report.append(f"Theoretical Average Gap: {theoretical_avg_gap:.1f}")
        else:
            report.append("No gap analysis data available.")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_recommendation_report(self, recommendations: Dict[str, Recommendation],
                                     frequency_data: Dict[int, int]) -> str:
        """
        Generate a comprehensive recommendation report.
        
        Args:
            recommendations: Dictionary of strategy recommendations
            frequency_data: Historical frequency data
            
        Returns:
            Formatted text report
        """
        self.logger.info("Generating recommendation report")
        
        report = []
        report.append("=" * 80)
        report.append("LOTTO MAX RECOMMENDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        if not recommendations:
            report.append("No recommendations available.")
            report.append("=" * 80)
            return "\n".join(report)
        
        # Overall summary
        report.append("RECOMMENDATION SUMMARY")
        report.append("-" * 40)
        report.append(f"Number of Strategies: {len(recommendations)}")
        
        avg_confidence = mean([rec.confidence for rec in recommendations.values()])
        report.append(f"Average Confidence: {avg_confidence:.2f}")
        report.append("")
        
        # Individual strategy reports
        for strategy_name, recommendation in recommendations.items():
            strategy_title = strategy_name.replace('_', ' ').title()
            report.append(f"{strategy_title} STRATEGY")
            report.append("-" * 40)
            
            # Numbers and basic info
            numbers_str = ", ".join([str(num) for num in recommendation.numbers])
            report.append(f"Recommended Numbers: {numbers_str}")
            report.append(f"Confidence Score: {recommendation.confidence:.2f}")
            report.append("")
            
            # Rationale
            report.append("Strategy Rationale:")
            wrapped_rationale = textwrap.fill(recommendation.rationale, width=70, initial_indent="  ", subsequent_indent="  ")
            report.append(wrapped_rationale)
            report.append("")
            
            # Number analysis
            report.append("Number Analysis:")
            frequencies = [frequency_data.get(num, 0) for num in recommendation.numbers]
            avg_frequency = mean(frequencies) if frequencies else 0
            overall_avg = mean(frequency_data.values()) if frequency_data else 0
            
            report.append(f"  Average Frequency: {avg_frequency:.1f}")
            report.append(f"  Overall Average: {overall_avg:.1f}")
            if overall_avg > 0:
                ratio = avg_frequency / overall_avg
                report.append(f"  Frequency Ratio: {ratio:.2f}x")
            
            # Odd/even analysis
            odd_count = sum(1 for num in recommendation.numbers if num % 2 == 1)
            even_count = 7 - odd_count
            report.append(f"  Odd/Even Split: {odd_count}-{even_count}")
            
            # Range distribution
            range_counts = {range_name: 0 for range_name in NUMBER_RANGES.keys()}
            for num in recommendation.numbers:
                for range_name, (min_val, max_val) in NUMBER_RANGES.items():
                    if min_val <= num <= max_val:
                        range_counts[range_name] += 1
                        break
            
            report.append("  Range Distribution:")
            for range_name, count in range_counts.items():
                if count > 0:
                    range_label = range_name.replace('_', ' ').title()
                    range_bounds = NUMBER_RANGES[range_name]
                    report.append(f"    {range_label} ({range_bounds[0]}-{range_bounds[1]}): {count} numbers")
            
            report.append("")
        
        # Strategy comparison
        if len(recommendations) > 1:
            report.append("STRATEGY COMPARISON")
            report.append("-" * 40)
            
            # Confidence comparison
            sorted_by_confidence = sorted(recommendations.items(), key=lambda x: x[1].confidence, reverse=True)
            report.append("Confidence Rankings:")
            for i, (strategy, rec) in enumerate(sorted_by_confidence, 1):
                strategy_title = strategy.replace('_', ' ').title()
                report.append(f"{i}. {strategy_title}: {rec.confidence:.2f}")
            report.append("")
            
            # Frequency comparison
            strategy_frequencies = {}
            for strategy, rec in recommendations.items():
                frequencies = [frequency_data.get(num, 0) for num in rec.numbers]
                avg_freq = mean(frequencies) if frequencies else 0
                strategy_frequencies[strategy] = avg_freq
            
            sorted_by_frequency = sorted(strategy_frequencies.items(), key=lambda x: x[1], reverse=True)
            report.append("Average Frequency Rankings:")
            for i, (strategy, avg_freq) in enumerate(sorted_by_frequency, 1):
                strategy_title = strategy.replace('_', ' ').title()
                report.append(f"{i}. {strategy_title}: {avg_freq:.1f}")
            report.append("")
            
            # Number overlap analysis
            all_numbers = set()
            for rec in recommendations.values():
                all_numbers.update(rec.numbers)
            
            report.append(f"Total Unique Numbers Across Strategies: {len(all_numbers)}")
            
            # Find common numbers
            if len(recommendations) >= 2:
                strategy_sets = {name: set(rec.numbers) for name, rec in recommendations.items()}
                common_numbers = set.intersection(*strategy_sets.values())
                if common_numbers:
                    common_str = ", ".join([str(num) for num in sorted(common_numbers)])
                    report.append(f"Numbers Common to All Strategies: {common_str}")
                else:
                    report.append("No numbers common to all strategies.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_comprehensive_report(self, draws: List[DrawResult],
                                    frequency_data: Dict[int, int],
                                    pattern_summary: Dict,
                                    recommendations: Dict[str, Recommendation],
                                    hot_numbers: List[int],
                                    cold_numbers: List[int]) -> str:
        """
        Generate a comprehensive analysis report combining all components.
        
        Args:
            draws: Historical draw data
            frequency_data: Number frequency data
            pattern_summary: Pattern analysis results
            recommendations: Strategy recommendations
            hot_numbers: Hot numbers list
            cold_numbers: Cold numbers list
            
        Returns:
            Complete formatted text report
        """
        self.logger.info("Generating comprehensive report")
        
        report_sections = []
        
        # Header
        report_sections.append("=" * 100)
        report_sections.append("LOTTO MAX COMPREHENSIVE ANALYSIS REPORT")
        report_sections.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append("=" * 100)
        report_sections.append("")
        
        # Executive summary
        if draws:
            total_draws = len(draws)
            date_range = f"{draws[0].date.strftime('%Y-%m-%d')} to {draws[-1].date.strftime('%Y-%m-%d')}"
            pattern_score = pattern_summary.get('pattern_score', 0)
            
            report_sections.append("EXECUTIVE SUMMARY")
            report_sections.append("-" * 50)
            report_sections.append(f"Analysis Period: {date_range}")
            report_sections.append(f"Total Draws Analyzed: {total_draws}")
            report_sections.append(f"Pattern Complexity Score: {pattern_score:.1f}/100")
            report_sections.append(f"Hot Numbers Identified: {len(hot_numbers)}")
            report_sections.append(f"Cold Numbers Identified: {len(cold_numbers)}")
            report_sections.append(f"Recommendation Strategies: {len(recommendations)}")
            report_sections.append("")
        
        # Individual reports
        frequency_report = self.generate_frequency_report(draws, frequency_data, hot_numbers, cold_numbers)
        pattern_report = self.generate_pattern_report(pattern_summary)
        recommendation_report = self.generate_recommendation_report(recommendations, frequency_data)
        
        # Combine all sections
        report_sections.extend([
            frequency_report,
            "",
            pattern_report,
            "",
            recommendation_report
        ])
        
        # Footer
        report_sections.append("")
        report_sections.append("=" * 100)
        report_sections.append("END OF REPORT")
        report_sections.append("=" * 100)
        
        return "\n".join(report_sections)
    
    def save_report(self, report_content: str, filename: str) -> str:
        """
        Save a report to a text file.
        
        Args:
            report_content: The report text content
            filename: Output filename (without extension)
            
        Returns:
            Full path to saved file
        """
        full_filename = f"{filename}.txt"
        
        try:
            with open(full_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Report saved to {full_filename}")
            return full_filename
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
            raise