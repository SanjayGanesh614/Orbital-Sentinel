import pandas as pd
import numpy as np
import os

class OmniDataLoader:
    def __init__(self, data_path="omni_data.csv", sequence_length=24):
        self.data_path = data_path
        self.sequence_length = sequence_length
        self.feature_cols = ['speed', 'density', 'bz', 'bt', 'kp']
        self.target_col = 'kp'

    def load_and_process(self):
        """
        Loads OMNI data (CSV), cleans fill values, and creates sequences.
        Expected CSV format: timestamp, speed, density, bz, bt, kp
        """
        if not os.path.exists(self.data_path):
            print(f"File {self.data_path} not found. Please download it from OMNIWeb.")
            return None, None

        # Load data
        df = pd.read_csv(self.data_path)
        
        # OMNI often uses 999.9 or 9999 as fill values for missing data
        # Replace common fill values with NaN and drop
        df = df.replace([999.9, 9999, 999], np.nan)
        df = df.dropna()
        
        # Scaling (Min-Max approximate for space weather)
        # Using fixed scalars for stability across training/inference
        df['speed'] = df['speed'] / 1000.0   # Max ~1000 km/s
        df['density'] = df['density'] / 100.0 # Max ~100 p/cc
        df['bz'] = (df['bz'] + 50) / 100.0   # Range -50 to 50 -> 0 to 1
        df['bt'] = df['bt'] / 50.0
        df['kp'] = df['kp'] / 9.0            # Kp is 0-9
        
        data = df[self.feature_cols].values
        
        X, y = [], []
        # Create sequences
        # Input: t-24 to t
        # Output: t+3 (Predicting 3 hours ahead)
        prediction_horizon = 3
        
        for i in range(len(data) - self.sequence_length - prediction_horizon):
            X.append(data[i : i + self.sequence_length])
            y.append(data[i + self.sequence_length + prediction_horizon - 1, 4]) # 4 is index of kp
            
        return np.array(X), np.array(y)

if __name__ == "__main__":
    # Create a dummy CSV for testing the loader if it doesn't exist
    if not os.path.exists("omni_data.csv"):
        print("Creating dummy dataset for demonstration...")
        dates = pd.date_range(start='2023-01-01', periods=500, freq='H')
        dummy_df = pd.DataFrame({
            'timestamp': dates,
            'speed': np.random.normal(400, 50, 500),
            'density': np.random.normal(5, 2, 500),
            'bz': np.random.normal(0, 5, 500),
            'bt': np.random.normal(5, 2, 500),
            'kp': np.random.randint(0, 9, 500)
        })
        dummy_df.to_csv("omni_data.csv", index=False)
        
    loader = OmniDataLoader()
    X, y = loader.load_and_process()
    print(f"Data Loaded. X shape: {X.shape}, y shape: {y.shape}")
