import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
try:
    from .data_loader import OmniDataLoader
except ImportError:
    from data_loader import OmniDataLoader
import numpy as np

# Check for GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# print(f"Using device: {device}") # Silence print on import

class SpaceWeatherLSTM(nn.Module):
    def __init__(self, input_dim=5, hidden_dim=64, num_layers=2, output_dim=1):
        super(SpaceWeatherLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # LSTM Layer
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        
        # Fully Connected Layer
        self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        # Initialize hidden state with zeros
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decode the hidden state of the last time step
        out = self.fc(out[:, -1, :])
        return out

def train_model():
    # 1. Load Data
    print("Loading Data...")
    loader = OmniDataLoader(sequence_length=24)
    X, y = loader.load_and_process()
    
    if X is None:
        return

    # Convert to PyTorch Tensors
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y, dtype=torch.float32).view(-1, 1).to(device) # Reshape for regression
    
    # Create Dataset
    dataset = TensorDataset(X_tensor, y_tensor)
    
    # Split
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [train_size, test_size])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32)
    
    # 2. Model, Loss, Optimizer
    model = SpaceWeatherLSTM().to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 3. Training Loop
    num_epochs = 50
    print("Starting Training...")
    
    for epoch in range(num_epochs):
        model.train()
        train_loss = 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        if (epoch+1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {train_loss/len(train_loader):.4f}')
            
    # 4. Save Model
    torch.save(model.state_dict(), "space_weather_lstm.pth")
    print("Model saved to space_weather_lstm.pth")
    
    # 5. Evaluate
    model.eval()
    with torch.no_grad():
        test_loss = 0
        for X_batch, y_batch in test_loader:
            outputs = model(X_batch)
            test_loss += criterion(outputs, y_batch).item()
        print(f"Test MSE: {test_loss/len(test_loader):.4f}")

if __name__ == "__main__":
    train_model()
