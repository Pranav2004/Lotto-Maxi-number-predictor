"""
Machine Learning Predictor for Lotto Max Analyzer.
Uses an LSTM (Long Short-Term Memory) neural network to predict future numbers
based on historical sequences.
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from typing import List, Dict
import logging

from ..data.models import DrawResult

class MLPredictor:
    """
    LSTM-based predictor for Lotto Max numbers.
    """

    def __init__(self, num_classes: int = 50, sequence_length: int = 10):
        """
        Initialize the ML Predictor.

        Args:
            num_classes: The number of possible lottery numbers (e.g., 50 for Lotto Max).
            sequence_length: The length of the sequence of past draws to consider for prediction.
        """
        self.num_classes = num_classes
        self.sequence_length = sequence_length
        self.model = None
        self.logger = logging.getLogger(__name__)
        self.is_trained = False

    def _prepare_data(self, historical_draws: List[DrawResult]) -> tuple:
        """
        Prepare historical data for LSTM training.
        """
        if len(historical_draws) <= self.sequence_length:
            return np.array([]), np.array([])

        # Flatten all numbers into a single list
        all_numbers = [num for draw in historical_draws for num in draw.numbers]

        # Create sequences
        X, y = [], []
        for i in range(len(all_numbers) - self.sequence_length):
            X.append(all_numbers[i:i + self.sequence_length])
            y.append(all_numbers[i + self.sequence_length])

        # Normalize and reshape data
        X = np.array(X) / self.num_classes
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        
        # One-hot encode the labels
        y = to_categorical([val - 1 for val in y], num_classes=self.num_classes)

        return X, y

    def build_model(self):
        """
        Build the LSTM model architecture.
        """
        self.model = Sequential([
            LSTM(128, input_shape=(self.sequence_length, 1), return_sequences=True),
            Dropout(0.2),
            LSTM(128),
            Dropout(0.2),
            Dense(self.num_classes, activation='softmax')
        ])
        self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        self.logger.info("LSTM model built successfully.")

    def train(self, historical_draws: List[DrawResult], epochs: int = 20, batch_size: int = 64):
        """
        Train the LSTM model on historical data.
        """
        if self.model is None:
            self.build_model()

        X, y = self._prepare_data(historical_draws)

        if X.shape[0] == 0:
            self.logger.warning("Not enough historical data to train the model.")
            return

        self.logger.info(f"Starting model training with {X.shape[0]} samples...")
        try:
            self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
            self.is_trained = True
            self.logger.info("Model training complete.")
        except Exception as e:
            self.logger.error(f"An error occurred during model training: {e}")
            self.is_trained = False

    def predict_probabilities(self, historical_draws: List[DrawResult]) -> Dict[int, float]:
        """
        Predict the probability of each number appearing in the next draw.
        """
        if not self.is_trained:
            self.logger.warning("Model is not trained. Cannot make predictions.")
            return {i: 1.0 / self.num_classes for i in range(1, self.num_classes + 1)}

        # Get the last sequence of numbers
        all_numbers = [num for draw in historical_draws for num in draw.numbers]
        last_sequence = all_numbers[-self.sequence_length:]

        # Normalize and reshape the input
        input_seq = np.array(last_sequence) / self.num_classes
        input_seq = np.reshape(input_seq, (1, self.sequence_length, 1))

        # Make prediction
        predicted_probabilities = self.model.predict(input_seq)[0]

        # Create a dictionary of number -> probability
        prob_dict = {i + 1: float(prob) for i, prob in enumerate(predicted_probabilities)}
        
        return prob_dict