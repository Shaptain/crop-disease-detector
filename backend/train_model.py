"""
train_model.py

Train a VGG16-based classifier on the full PlantVillage dataset (38 classes) using PyTorch.
Outputs: model/plant_disease_model.pth + model/class_labels.json + model/training_metrics.json
"""

import kagglehub
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import precision_recall_fscore_support, classification_report, confusion_matrix
from PIL import Image
import json
import os
import time
import numpy as np

# -- Config ------------------------------------------------------------------
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "model")
MODEL_SAVE_PATH = os.path.join(MODEL_DIR, "plant_disease_model.pth")
LABELS_SAVE_PATH = os.path.join(MODEL_DIR, "class_labels.json")
METRICS_SAVE_PATH = os.path.join(MODEL_DIR, "training_metrics.json")

print(f"Device: {DEVICE}")
if DEVICE == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")


# -- Find data root ----------------------------------------------------------
def find_data_root(base_path):
    """
    Auto-detect the dataset root. Handles two layouts:
    1. Pre-split: root/train/ and root/val/ each containing class dirs
    2. Flat: root/ directly containing class dirs
    Returns (root, is_presplit) where root is the parent of class dirs (or train/).
    """
    # Build candidate list
    candidates = [base_path]
    for child in os.listdir(base_path):
        child_path = os.path.join(base_path, child)
        if os.path.isdir(child_path):
            candidates.append(child_path)
            # Go one level deeper (e.g. base/PlantVillage/train)
            for grandchild in os.listdir(child_path):
                gc_path = os.path.join(child_path, grandchild)
                if os.path.isdir(gc_path):
                    candidates.append(gc_path)

    # Check for pre-split layout: a folder containing train/ and val/ subdirs
    for candidate in candidates:
        train_dir = os.path.join(candidate, "train")
        val_dir = os.path.join(candidate, "val")
        if os.path.isdir(train_dir) and os.path.isdir(val_dir):
            train_classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
            if len(train_classes) >= 10:
                return candidate, True

    # Check for flat layout: folder with 10+ class subdirs with '___' in name
    for candidate in candidates:
        subdirs = [
            d for d in os.listdir(candidate)
            if os.path.isdir(os.path.join(candidate, d)) and "___" in d
        ]
        if len(subdirs) >= 10:
            return candidate, False

    return base_path, False


# -- Download / locate dataset -----------------------------------------------
print("Locating dataset...")
dataset_path = kagglehub.dataset_download("mohitsingh1804/plantvillage")
data_dir, is_presplit = find_data_root(dataset_path)
print(f"Data root: {data_dir} (pre-split: {is_presplit})")

SKIP_DIRS = {"PlantVillage", ".ipynb_checkpoints", "__pycache__", "train", "val", "test"}

if is_presplit:
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    class_dirs = sorted([
        d for d in os.listdir(train_dir)
        if os.path.isdir(os.path.join(train_dir, d)) and d not in SKIP_DIRS
    ])
    scan_dirs = [train_dir, val_dir]
else:
    train_dir = data_dir
    val_dir = None
    class_dirs = sorted([
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d)) and d not in SKIP_DIRS
    ])
    scan_dirs = [data_dir]

NUM_CLASSES = len(class_dirs)
total_images = 0
for sd in scan_dirs:
    for cd in class_dirs:
        cd_path = os.path.join(sd, cd)
        if os.path.isdir(cd_path):
            total_images += len([f for f in os.listdir(cd_path) if os.path.isfile(os.path.join(cd_path, f))])
print(f"Found {NUM_CLASSES} classes, {total_images} images")

# -- Clean corrupt images before loading -------------------------------------
print("Scanning for corrupt images...")
removed = 0
for sd in scan_dirs:
    for cls_dir in class_dirs:
        cls_path = os.path.join(sd, cls_dir)
        if not os.path.isdir(cls_path):
            continue
        for fname in os.listdir(cls_path):
            fpath = os.path.join(cls_path, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with Image.open(fpath) as img:
                    img.verify()
            except Exception:
                print(f"  Removing corrupt: {fpath}")
                os.remove(fpath)
                removed += 1
print(f"Removed {removed} corrupt images")

# -- Data transforms ---------------------------------------------------------
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


# -- Load dataset ------------------------------------------------------------
print("Loading dataset...")

if is_presplit:
    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)
    CLASS_LABELS = [c for c in train_dataset.classes if c not in SKIP_DIRS]
else:
    full_dataset = datasets.ImageFolder(data_dir, transform=train_transform)
    CLASS_LABELS = [c for c in full_dataset.classes if c not in SKIP_DIRS]
    total = len(full_dataset)
    train_size = int(0.8 * total)
    val_size = total - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42),
    )

train_size = len(train_dataset)
val_size = len(val_dataset)
print(f"Class labels ({len(CLASS_LABELS)}): {CLASS_LABELS}")

NUM_WORKERS = 0  # Windows doesn't support fork-based multiprocessing
train_loader = DataLoader(
    train_dataset, batch_size=BATCH_SIZE, shuffle=True,
    num_workers=NUM_WORKERS, pin_memory=(DEVICE == "cuda"),
)
val_loader = DataLoader(
    val_dataset, batch_size=BATCH_SIZE, shuffle=False,
    num_workers=NUM_WORKERS, pin_memory=(DEVICE == "cuda"),
)

print(f"Train: {train_size}, Val: {val_size}")

# -- Build VGG16 model -------------------------------------------------------
print("\nBuilding VGG16 model...")
model = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)

# Freeze all backbone layers first
for param in model.features.parameters():
    param.requires_grad = False

# Unfreeze the last conv block (features[24:] = conv5) for fine-tuning
for param in model.features[24:].parameters():
    param.requires_grad = True

# Replace classifier head
model.classifier = nn.Sequential(
    nn.Linear(512 * 7 * 7, 256),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(256, NUM_CLASSES),
)

model = model.to(DEVICE)
print(f"Model parameters (trainable): {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=LEARNING_RATE)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

# -- Train -------------------------------------------------------------------
print("\nTraining...")
best_val_acc = 0.0
patience_counter = 0
PATIENCE = 3
training_history = []

for epoch in range(EPOCHS):
    start = time.time()

    # Train phase
    model.train()
    train_loss, train_correct, train_total = 0.0, 0, 0
    for batch_idx, (images, labels) in enumerate(train_loader):
        images, labels = images.to(DEVICE), labels.to(DEVICE)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * images.size(0)
        train_correct += (outputs.argmax(1) == labels).sum().item()
        train_total += images.size(0)

        if (batch_idx + 1) % 50 == 0:
            print(f"  Epoch {epoch+1} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {loss.item():.4f}")

    # Val phase — collect all predictions for metrics
    model.eval()
    val_loss, val_correct, val_total = 0.0, 0, 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item() * images.size(0)
            preds = outputs.argmax(1)
            val_correct += (preds == labels).sum().item()
            val_total += images.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    train_acc = train_correct / train_total
    val_acc = val_correct / val_total
    train_loss /= train_total
    val_loss /= val_total
    elapsed = time.time() - start

    # Compute macro metrics
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="macro", zero_division=0
    )

    current_lr = optimizer.param_groups[0]["lr"]

    # Log epoch metrics
    epoch_metrics = {
        "epoch": epoch + 1,
        "train_loss": round(train_loss, 4),
        "train_accuracy": round(train_acc, 4),
        "val_loss": round(val_loss, 4),
        "val_accuracy": round(val_acc, 4),
        "val_precision_macro": round(float(precision_macro), 4),
        "val_recall_macro": round(float(recall_macro), 4),
        "val_f1_macro": round(float(f1_macro), 4),
        "learning_rate": current_lr,
        "time_seconds": round(elapsed, 1),
    }
    training_history.append(epoch_metrics)

    print(
        f"Epoch {epoch+1}/{EPOCHS} | "
        f"Train Loss: {train_loss:.4f} Acc: {train_acc*100:.2f}% | "
        f"Val Loss: {val_loss:.4f} Acc: {val_acc*100:.2f}% | "
        f"P: {precision_macro:.3f} R: {recall_macro:.3f} F1: {f1_macro:.3f} | "
        f"LR: {current_lr:.1e} | {elapsed:.0f}s"
    )

    scheduler.step(val_loss)

    # Early stopping
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        patience_counter = 0
        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save({
            "model_state_dict": model.state_dict(),
            "class_labels": CLASS_LABELS,
            "num_classes": NUM_CLASSES,
            "val_accuracy": val_acc,
        }, MODEL_SAVE_PATH)
        print(f"  -> Saved best model (val_acc={val_acc*100:.2f}%)")
    else:
        patience_counter += 1
        if patience_counter >= PATIENCE:
            print(f"Early stopping at epoch {epoch+1}")
            break

# -- Final evaluation on best model ------------------------------------------
print("\nRunning final evaluation on best model...")
checkpoint = torch.load(MODEL_SAVE_PATH, map_location=DEVICE, weights_only=False)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

all_preds = []
all_labels = []
with torch.no_grad():
    for images, labels in val_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        outputs = model(images)
        preds = outputs.argmax(1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

all_preds = np.array(all_preds)
all_labels = np.array(all_labels)

# Per-class metrics
report = classification_report(
    all_labels, all_preds,
    target_names=CLASS_LABELS,
    output_dict=True,
    zero_division=0,
)

per_class_metrics = {}
for label in CLASS_LABELS:
    if label in report:
        per_class_metrics[label] = {
            "precision": round(report[label]["precision"], 4),
            "recall": round(report[label]["recall"], 4),
            "f1": round(report[label]["f1-score"], 4),
            "support": int(report[label]["support"]),
        }

# Confusion matrix
cm = confusion_matrix(all_labels, all_preds)

# Macro averages
macro_avg = report.get("macro avg", {})

# -- Save metrics JSON -------------------------------------------------------
metrics = {
    "dataset": "mohitsingh1804/plantvillage",
    "num_classes": NUM_CLASSES,
    "class_labels": CLASS_LABELS,
    "total_images": total_images,
    "train_size": train_size,
    "val_size": val_size,
    "best_val_accuracy": round(best_val_acc, 4),
    "training_history": training_history,
    "final_evaluation": {
        "per_class_metrics": per_class_metrics,
        "macro_avg": {
            "precision": round(macro_avg.get("precision", 0), 4),
            "recall": round(macro_avg.get("recall", 0), 4),
            "f1": round(macro_avg.get("f1-score", 0), 4),
        },
        "confusion_matrix": cm.tolist(),
    },
}

os.makedirs(MODEL_DIR, exist_ok=True)
with open(METRICS_SAVE_PATH, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"Metrics saved to {METRICS_SAVE_PATH}")

# -- Save class labels -------------------------------------------------------
with open(LABELS_SAVE_PATH, "w") as f:
    json.dump(CLASS_LABELS, f, indent=2)
print(f"Class labels saved to {LABELS_SAVE_PATH}")
print(f"Best validation accuracy: {best_val_acc*100:.2f}%")
print("Done!")
