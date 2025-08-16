"""Data storage module for Lotto Max draw results."""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from .models import DrawResult
from ..config import DATABASE_FILE


class DataStorage:
    """Handles SQLite database operations for Lotto Max draw results."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the data storage with database path."""
        self.db_path = db_path or DATABASE_FILE
        self.logger = logging.getLogger(__name__)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Create database and tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                self._create_tables(conn)
                self.logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create the draws table and indexes."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date DATE NOT NULL,
            number_1 INTEGER NOT NULL,
            number_2 INTEGER NOT NULL,
            number_3 INTEGER NOT NULL,
            number_4 INTEGER NOT NULL,
            number_5 INTEGER NOT NULL,
            number_6 INTEGER NOT NULL,
            number_7 INTEGER NOT NULL,
            bonus_number INTEGER NOT NULL,
            jackpot_amount REAL NOT NULL,
            draw_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create indexes for better query performance
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_draw_date ON draws(draw_date);",
            "CREATE INDEX IF NOT EXISTS idx_jackpot ON draws(jackpot_amount);",
            "CREATE INDEX IF NOT EXISTS idx_draw_id ON draws(draw_id);"
        ]
        
        conn.execute(create_table_sql)
        for index_sql in create_indexes_sql:
            conn.execute(index_sql)
        
        conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_draws(self, draws: List[DrawResult]) -> int:
        """
        Save multiple draw results to the database.
        
        Args:
            draws: List of DrawResult objects to save
            
        Returns:
            Number of draws successfully saved
            
        Raises:
            ValueError: If draws list is empty or contains invalid data
            sqlite3.Error: If database operation fails
        """
        if not draws:
            raise ValueError("Cannot save empty draws list")
        
        saved_count = 0
        
        with self._get_connection() as conn:
            for draw in draws:
                try:
                    self._save_single_draw(conn, draw)
                    saved_count += 1
                except sqlite3.IntegrityError:
                    # Draw already exists, skip it
                    self.logger.debug(f"Draw {draw.draw_id} already exists, skipping")
                    continue
                except Exception as e:
                    self.logger.error(f"Failed to save draw {draw.draw_id}: {e}")
                    continue
            
            conn.commit()
        
        self.logger.info(f"Saved {saved_count} out of {len(draws)} draws")
        return saved_count
    
    def _save_single_draw(self, conn: sqlite3.Connection, draw: DrawResult):
        """Save a single draw result to the database."""
        insert_sql = """
        INSERT INTO draws (
            draw_date, number_1, number_2, number_3, number_4, 
            number_5, number_6, number_7, bonus_number, 
            jackpot_amount, draw_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Ensure numbers are sorted for consistency
        sorted_numbers = sorted(draw.numbers)
        
        values = (
            draw.date.date(),
            *sorted_numbers,
            draw.bonus,
            draw.jackpot_amount,
            draw.draw_id
        )
        
        conn.execute(insert_sql, values)
    
    def load_draws(self, start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None) -> List[DrawResult]:
        """
        Load draw results from the database within date range.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of DrawResult objects
        """
        query = "SELECT * FROM draws"
        params = []
        
        # Build WHERE clause for date filtering
        where_conditions = []
        if start_date:
            where_conditions.append("draw_date >= ?")
            params.append(start_date.date())
        
        if end_date:
            where_conditions.append("draw_date <= ?")
            params.append(end_date.date())
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " ORDER BY draw_date DESC"
        
        draws = []
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                draws.append(self._row_to_draw_result(row))
        
        self.logger.info(f"Loaded {len(draws)} draws from database")
        return draws
    
    def get_all_draws(self) -> List[DrawResult]:
        """Get all draw results from the database."""
        return self.load_draws()
    
    def get_draw_by_id(self, draw_id: str) -> Optional[DrawResult]:
        """Get a specific draw by its ID."""
        query = "SELECT * FROM draws WHERE draw_id = ?"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, (draw_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_draw_result(row)
            return None
    
    def get_latest_draw(self) -> Optional[DrawResult]:
        """Get the most recent draw from the database."""
        query = "SELECT * FROM draws ORDER BY draw_date DESC LIMIT 1"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query)
            row = cursor.fetchone()
            
            if row:
                return self._row_to_draw_result(row)
            return None
    
    def get_draw_count(self) -> int:
        """Get the total number of draws in the database."""
        query = "SELECT COUNT(*) FROM draws"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query)
            return cursor.fetchone()[0]
    
    def delete_draw(self, draw_id: str) -> bool:
        """
        Delete a draw by its ID.
        
        Args:
            draw_id: The ID of the draw to delete
            
        Returns:
            True if draw was deleted, False if not found
        """
        query = "DELETE FROM draws WHERE draw_id = ?"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, (draw_id,))
            conn.commit()
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.logger.info(f"Deleted draw {draw_id}")
            else:
                self.logger.warning(f"Draw {draw_id} not found for deletion")
            
            return deleted
    
    def _row_to_draw_result(self, row: sqlite3.Row) -> DrawResult:
        """Convert database row to DrawResult object."""
        numbers = [
            row['number_1'], row['number_2'], row['number_3'], row['number_4'],
            row['number_5'], row['number_6'], row['number_7']
        ]
        
        return DrawResult(
            date=datetime.strptime(row['draw_date'], '%Y-%m-%d'),
            numbers=numbers,
            bonus=row['bonus_number'],
            jackpot_amount=row['jackpot_amount'],
            draw_id=row['draw_id']
        )