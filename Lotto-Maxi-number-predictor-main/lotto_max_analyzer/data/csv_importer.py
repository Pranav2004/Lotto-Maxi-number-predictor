"""
CSV Import utility for Lotto Max historical data.
This allows importing real lottery data from official CSV files.
"""

import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .models import DrawResult
from .storage import DataStorage


class CSVImporter:
    """Import Lotto Max data from CSV files."""
    
    def __init__(self):
        """Initialize the CSV importer."""
        self.logger = logging.getLogger(__name__)
        self.storage = DataStorage()
    
    def import_from_csv(self, csv_path: Path, format_type: str = 'auto') -> int:
        """
        Import Lotto Max data from CSV file.
        
        Args:
            csv_path: Path to CSV file
            format_type: CSV format ('olg', 'generic', 'auto')
            
        Returns:
            Number of draws imported
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.logger.info(f"Importing Lotto Max data from {csv_path}")
        
        # Detect format if auto
        if format_type == 'auto':
            format_type = self._detect_csv_format(csv_path)
            self.logger.info(f"Detected CSV format: {format_type}")
        
        # Import based on format
        if format_type == 'olg':
            draws = self._import_olg_format(csv_path)
        elif format_type == 'generic':
            draws = self._import_generic_format(csv_path)
        elif format_type == 'lotterypost':
            draws = self._import_lotterypost_format(csv_path)
        else:
            raise ValueError(f"Unsupported CSV format: {format_type}")
        
        # Save to database
        saved_count = self.storage.save_draws(draws)
        self.logger.info(f"Imported {saved_count} draws from CSV")
        
        return saved_count
    
    def _detect_csv_format(self, csv_path: Path) -> str:
        """Detect the CSV format by examining headers."""
        try:
            # Read first few lines to detect format
            with open(csv_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().lower()
                
            if 'olg' in first_line or 'ontario' in first_line:
                return 'olg'
            elif 'lotterypost' in first_line:
                return 'lotterypost'
            elif any(word in first_line for word in ['date', 'numbers', 'bonus', 'jackpot']):
                return 'generic'
            else:
                return 'generic'  # Default fallback
                
        except Exception:
            return 'generic'
    
    def _import_olg_format(self, csv_path: Path) -> List[DrawResult]:
        """Import from OLG (Ontario Lottery) CSV format."""
        draws = []
        
        try:
            df = pd.read_csv(csv_path)
            
            # Common OLG column names (may vary)
            date_cols = ['Date', 'Draw Date', 'DRAW_DATE', 'date']
            number_cols = ['Numbers', 'Winning Numbers', 'NUMBERS', 'numbers']
            bonus_cols = ['Bonus', 'Bonus Number', 'BONUS', 'bonus']
            jackpot_cols = ['Jackpot', 'Prize', 'JACKPOT', 'jackpot']
            
            # Find actual column names
            date_col = self._find_column(df, date_cols)
            numbers_col = self._find_column(df, number_cols)
            bonus_col = self._find_column(df, bonus_cols)
            jackpot_col = self._find_column(df, jackpot_cols)
            
            for _, row in df.iterrows():
                try:
                    # Parse date
                    date_str = str(row[date_col])
                    draw_date = self._parse_date(date_str)
                    
                    # Parse numbers
                    numbers_str = str(row[numbers_col])
                    numbers = self._parse_numbers(numbers_str)
                    
                    # Parse bonus
                    bonus_str = str(row[bonus_col]) if bonus_col else "1"
                    bonus = self._parse_bonus(bonus_str, numbers)
                    
                    # Parse jackpot
                    jackpot_str = str(row[jackpot_col]) if jackpot_col else "10000000"
                    jackpot = self._parse_jackpot(jackpot_str)
                    
                    # Create draw
                    draw = DrawResult(
                        date=draw_date,
                        numbers=sorted(numbers),
                        bonus=bonus,
                        jackpot_amount=jackpot,
                        draw_id=f"CSV-{draw_date.strftime('%Y%m%d')}"
                    )
                    
                    draws.append(draw)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Failed to read OLG CSV: {e}")
            raise
        
        return draws
    
    def _import_generic_format(self, csv_path: Path) -> List[DrawResult]:
        """Import from generic CSV format."""
        draws = []
        
        try:
            df = pd.read_csv(csv_path)
            
            # Try to auto-detect columns
            for _, row in df.iterrows():
                try:
                    # Look for date in first few columns
                    draw_date = None
                    for col in df.columns[:3]:
                        try:
                            draw_date = self._parse_date(str(row[col]))
                            break
                        except:
                            continue
                    
                    if not draw_date:
                        continue
                    
                    # Look for numbers (should be 7 numbers)
                    numbers = None
                    for col in df.columns:
                        try:
                            numbers = self._parse_numbers(str(row[col]))
                            if len(numbers) == 7:
                                break
                        except:
                            continue
                    
                    if not numbers or len(numbers) != 7:
                        continue
                    
                    # Look for bonus
                    bonus = 1  # Default
                    for col in df.columns:
                        if 'bonus' in col.lower():
                            try:
                                bonus = self._parse_bonus(str(row[col]), numbers)
                                break
                            except:
                                continue
                    
                    # Look for jackpot
                    jackpot = 10_000_000  # Default
                    for col in df.columns:
                        if any(word in col.lower() for word in ['jackpot', 'prize', 'amount']):
                            try:
                                jackpot = self._parse_jackpot(str(row[col]))
                                break
                            except:
                                continue
                    
                    # Create draw
                    draw = DrawResult(
                        date=draw_date,
                        numbers=sorted(numbers),
                        bonus=bonus,
                        jackpot_amount=jackpot,
                        draw_id=f"CSV-{draw_date.strftime('%Y%m%d')}"
                    )
                    
                    draws.append(draw)
                    
                except Exception as e:
                    self.logger.debug(f"Failed to parse row: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Failed to read generic CSV: {e}")
            raise
        
        return draws
    
    def _import_lotterypost_format(self, csv_path: Path) -> List[DrawResult]:
        """Import from LotteryPost.com CSV format."""
        # Similar to generic but with specific column expectations
        return self._import_generic_format(csv_path)
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by possible names."""
        for col in df.columns:
            if col in possible_names:
                return col
            # Case-insensitive match
            for name in possible_names:
                if col.lower() == name.lower():
                    return col
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from various formats."""
        date_str = date_str.strip()
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%b %d, %Y',
            '%B %d, %Y',
            '%d-%m-%Y',
            '%Y%m%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_str}")
    
    def _parse_numbers(self, numbers_str: str) -> List[int]:
        """Parse winning numbers from string."""
        # Clean up the string
        numbers_str = numbers_str.replace('[', '').replace(']', '')
        numbers_str = numbers_str.replace('(', '').replace(')', '')
        
        # Split by various delimiters
        import re
        numbers = re.findall(r'\d+', numbers_str)
        
        # Convert to integers
        numbers = [int(n) for n in numbers if 1 <= int(n) <= 50]
        
        if len(numbers) < 7:
            raise ValueError(f"Not enough valid numbers found: {numbers}")
        
        # Take first 7 numbers
        return numbers[:7]
    
    def _parse_bonus(self, bonus_str: str, main_numbers: List[int]) -> int:
        """Parse bonus number."""
        try:
            bonus = int(bonus_str.strip())
            if 1 <= bonus <= 50 and bonus not in main_numbers:
                return bonus
        except:
            pass
        
        # Generate a valid bonus if parsing fails
        available = [n for n in range(1, 51) if n not in main_numbers]
        return available[0] if available else 1
    
    def _parse_jackpot(self, jackpot_str: str) -> float:
        """Parse jackpot amount."""
        try:
            # Clean up string
            jackpot_str = jackpot_str.replace('$', '').replace(',', '').strip()
            
            # Handle millions
            if 'M' in jackpot_str.upper():
                amount = float(jackpot_str.upper().replace('M', '')) * 1_000_000
            else:
                amount = float(jackpot_str)
            
            return max(amount, 0)
            
        except:
            return 10_000_000  # Default jackpot
    
    def create_sample_csv(self, output_path: Path):
        """Create a sample CSV file showing the expected format."""
        sample_data = [
            ['Date', 'Numbers', 'Bonus', 'Jackpot'],
            ['2025-08-15', '4 9 19 21 27 41 44', '11', '70000000'],
            ['2025-08-13', '2 8 15 23 31 38 45', '7', '65000000'],
            ['2025-08-10', '1 12 18 25 33 40 47', '3', '60000000'],
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(sample_data)
        
        print(f"✅ Sample CSV created at: {output_path}")
        print("📝 Edit this file with real Lotto Max data and import it!")


def import_csv_data(csv_path: str) -> int:
    """Convenience function to import CSV data."""
    importer = CSVImporter()
    return importer.import_from_csv(Path(csv_path))


if __name__ == "__main__":
    # Create sample CSV for testing
    importer = CSVImporter()
    sample_path = Path("sample_lotto_max_data.csv")
    importer.create_sample_csv(sample_path)
    
    print("\n🎯 CSV Import Instructions:")
    print("1. Download official Lotto Max CSV data from lottery websites")
    print("2. Or edit the sample CSV file with real data")
    print("3. Run: python -c \"from lotto_max_analyzer.data.csv_importer import import_csv_data; import_csv_data('your_file.csv')\"")