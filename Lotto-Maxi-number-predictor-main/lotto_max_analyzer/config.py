"""Configuration settings for Lotto Max Analyzer."""

import os
from pathlib import Path

# Application settings
APP_NAME = "Lotto Max Analyzer"
VERSION = "1.0.0"

# Database settings
DATABASE_DIR = Path.home() / ".lotto_max_analyzer"
DATABASE_FILE = DATABASE_DIR / "lotto_max.db"

# Ensure database directory exists
DATABASE_DIR.mkdir(exist_ok=True)

# Lotto Max game constants
LOTTO_MAX_MIN_NUMBER = 1
LOTTO_MAX_MAX_NUMBER = 50
LOTTO_MAX_NUMBERS_COUNT = 7
LOTTO_MAX_BONUS_COUNT = 1

# Analysis settings
MIN_DRAWS_FOR_ANALYSIS = 50
HOT_NUMBER_THRESHOLD = 0.7  # Numbers appearing more than 70% of expected frequency
COLD_NUMBER_THRESHOLD = 0.3  # Numbers appearing less than 30% of expected frequency

# Data fetching settings
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
RATE_LIMIT_DELAY = 0.5  # seconds between requests

# Visualization settings
CHART_WIDTH = 12
CHART_HEIGHT = 8
CHART_DPI = 100
COLOR_HOT = '#FF6B6B'  # Red for hot numbers
COLOR_COLD = '#4ECDC4'  # Teal for cold numbers
COLOR_NEUTRAL = '#95A5A6'  # Gray for neutral numbers

# Date ranges
DEFAULT_ANALYSIS_YEARS = 2  # Analyze last 2 years by default

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Number ranges for analysis
NUMBER_RANGES = {
    'low': (1, 10),
    'mid_low': (11, 20),
    'mid': (21, 30),
    'mid_high': (31, 40),
    'high': (41, 50)
}