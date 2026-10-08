"""
AJAX AI - GPU-Accelerated Neural Intent Training Engine
Auto-detects NVIDIA CUDA, AMD/Intel DirectML, or multi-threaded CPU acceleration
and trains a PyTorch Neural Network Intent Classifier.
"""

import sys
import os
import json
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

INTENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "intents.json")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ----------------- DEVICE SELECTOR (CUDA / DirectML / CPU) ----------------- #
def get_acceleration_device():
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        return torch.device("cuda"), f"NVIDIA CUDA GPU ({device_name})"
    try:
        import torch_directml
        if torch_directml.is_available():
            return torch_directml.device(), "DirectML GPU Accelerator (AMD / Intel / Windows GPU)"
    except Exception:
        pass
    return torch.device("cpu"), f"High-Performance Multi-Threaded CPU ({torch.get_num_threads()} threads)"

# ----------------- PYTORCH NEURAL INTENT NETWORK ----------------- #
class NeuralIntentNet(nn.Module):
    def __init__(self, vocab_size: int, hidden_dim: int, num_classes: int):
        super(NeuralIntentNet, self).__init__()
        self.fc1 = nn.Linear(vocab_size, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, num_classes)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.fc3(out)
        return out

def train_gpu_intent_model(epochs: int = 40, batch_size: int = 32, lr: float = 0.005):
    print("\n==================================================================")
    print("  [GPU NEURAL ACCELERATION] PYTORCH DEEP LEARNING TRAINER")
    print("==================================================================")

    device, device_desc = get_acceleration_device()
    print(f"  * Compute Target       : {device_desc}")
    print(f"  * PyTorch Framework    : {torch.__version__}")
    print(f"  * Training Epochs      : {epochs}")
    print(f"  * Batch Size           : {batch_size}")
    print("==================================================================\n")

    if not os.path.exists(INTENTS_FILE):
        print("Intents dataset missing.")
        return

    with open(INTENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    intents = data.get("intents", [])
    intent_labels = [item["intent"] for item in intents]
    intent_to_idx = {name: i for i, name in enumerate(intent_labels)}

    # Build Vocabulary
    vocab = set()
    samples = []
    for item in intents:
        lbl_idx = intent_to_idx[item["intent"]]
        for p in item["patterns"]:
            tokens = p.lower().split()
            vocab.update(tokens)
            samples.append((tokens, lbl_idx))

    vocab_list = sorted(list(vocab))
    word_to_idx = {w: i for i, w in enumerate(vocab_list)}
    vocab_size = len(vocab_list)
    num_classes = len(intent_labels)

    print(f"[1/4] Vectorizing Dataset: {len(samples)} patterns across {num_classes} intents (Vocab: {vocab_size} words)...")

    X = torch.zeros((len(samples), vocab_size), dtype=torch.float32)
    y = torch.zeros(len(samples), dtype=torch.long)

    for row_idx, (tokens, lbl_idx) in enumerate(samples):
        for t in tokens:
            if t in word_to_idx:
                X[row_idx, word_to_idx[t]] += 1.0
        y[row_idx] = lbl_idx

    # Move tensors to GPU/Target Device
    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print(f"[2/4] Allocating Neural Network Weights on {device_desc}...")
    model = NeuralIntentNet(vocab_size=vocab_size, hidden_dim=128, num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    print(f"[3/4] Launching GPU/CPU Training Loop...")
    start_time = time.time()

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        correct = 0
        total = 0

        for batch_X, batch_y in loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            correct += (preds == batch_y).sum().item()
            total += batch_y.size(0)

        acc = (correct / total) * 100
        if epoch % 10 == 0 or epoch == 1:
            print(f"  Epoch [{epoch:2d}/{epochs}] | Loss: {total_loss/len(loader):.4f} | Training Accuracy: {acc:.1f}%")

    duration = time.time() - start_time
    print(f"\n[4/4] Training Complete in {duration:.2f}s! Saving Neural Model Weights...")

    model_save_path = os.path.join(MODELS_DIR, "ajax_neural_intent.pt")
    vocab_save_path = os.path.join(MODELS_DIR, "vocab_metadata.json")

    torch.save(model.state_dict(), model_save_path)
    with open(vocab_save_path, "w", encoding="utf-8") as f:
        json.dump({
            "word_to_idx": word_to_idx,
            "intent_labels": intent_labels,
            "vocab_size": vocab_size,
            "num_classes": num_classes
        }, f, indent=2)

    print("==================================================================")
    print(f"  [SUCCESS] GPU NEURAL MODEL TRAINED & SAVED!")
    print(f"  * Model Checkpoint : {model_save_path}")
    print(f"  * Vocab Metadata   : {vocab_save_path}")
    print("==================================================================\n")

if __name__ == "__main__":
    train_gpu_intent_model()
