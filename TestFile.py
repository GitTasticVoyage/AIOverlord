import torch
import torch.nn as nn
import time

device_cpu = torch.device("cpu")
device_gpu = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Use a deeper model
model = nn.Sequential(
    nn.Linear(1000, 2000), nn.ReLU(),
    nn.Linear(2000, 2000), nn.ReLU(),
    nn.Linear(2000, 1000), nn.ReLU(),
    nn.Linear(1000, 1)
)

# Larger dataset
data = torch.randn(50000, 1000)
target = torch.randn(50000, 1)
loss_fn = nn.MSELoss()

def train_on(device):
    model_d = model.to(device)
    x = data.to(device)
    y = target.to(device)
    optimizer = torch.optim.SGD(model_d.parameters(), lr=0.01)

    if device.type == 'cuda':
        torch.cuda.synchronize()
    start = time.time()

    for _ in range(100):  # more iterations
        optimizer.zero_grad()
        pred = model_d(x)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()

    if device.type == 'cuda':
        torch.cuda.synchronize()
    end = time.time()

    print(f"Training on {device}: {end - start:.2f} seconds")

# train_on(device_cpu)
train_on(device_gpu)