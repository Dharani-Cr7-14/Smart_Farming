import os
import shutil
import json
import random
from pathlib import Path

# Root project directory
ROOT_DIR = Path(__file__).resolve().parents[2]

# Dataset paths
raw_dataset = os.path.join(ROOT_DIR, "data", "PlantVillage-Dataset")   # <-- updated here
output_dataset = os.path.join(ROOT_DIR, "data", "plant_disease")

# Train/val/test split ratios
SPLIT_RATIOS = {"train": 0.7, "val": 0.2, "test": 0.1}


def split_dataset(base_dir, output_dir):
    class_indices = {}

    # Loop through class folders (e.g., Tomato___Early_blight, Strawberry___healthy, etc.)
    for idx, class_name in enumerate(os.listdir(base_dir)):
        class_path = os.path.join(base_dir, class_name)
        if not os.path.isdir(class_path):
            continue

        class_indices[class_name] = idx
        images = os.listdir(class_path)
        random.shuffle(images)

        n_total = len(images)
        n_train = int(n_total * SPLIT_RATIOS["train"])
        n_val = int(n_total * SPLIT_RATIOS["val"])

        split_data = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:]
        }

        for split, split_images in split_data.items():
            split_dir = os.path.join(output_dir, split, class_name)
            os.makedirs(split_dir, exist_ok=True)
            for img in split_images:
                src = os.path.join(class_path, img)
                dst = os.path.join(split_dir, img)
                shutil.copy2(src, dst)

    # Save class-to-index mapping
    with open(os.path.join(output_dir, "class_indices.json"), "w") as f:
        json.dump(class_indices, f, indent=4)

    print(f"✅ Dataset split completed. Saved in {output_dir}")


if __name__ == "__main__":
    split_dataset(raw_dataset, output_dataset)
