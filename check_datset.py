import os
from PIL import Image

# Path to your dataset
dataset_dir = r"C:\Users\aarth\uzhavan_saathee\data\plant_disease"

splits = ["train", "val", "test"]

# Step 1: Check folder structure
print("Checking folder structure and classes...\n")
all_classes = {}

for split in splits:
    split_path = os.path.join(dataset_dir, split)
    if not os.path.exists(split_path):
        print(f"❌ Missing folder: {split}")
        continue

    classes = [d for d in os.listdir(split_path) if os.path.isdir(os.path.join(split_path, d))]
    all_classes[split] = classes
    print(f"{split} has classes: {classes}")

# Step 2: Check if all splits have the same classes
common_classes = set(all_classes.get("train", []))
for split in splits[1:]:
    diff = common_classes.symmetric_difference(set(all_classes.get(split, [])))
    if diff:
        print(f"⚠️ Classes mismatch in {split}: {diff}")
    else:
        print(f"✅ Classes in {split} match train set")

# Step 3: Check number of images per class
print("\nChecking number of images per class...")
for split in splits:
    print(f"\n{split}:")
    for class_name in all_classes[split]:
        class_path = os.path.join(dataset_dir, split, class_name)
        images = [f for f in os.listdir(class_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        print(f"  {class_name}: {len(images)} images")

# Step 4: Check image sizes (first 3 images per class)
print("\nChecking image sizes (first 3 images per class)...")
for split in splits:
    print(f"\n{split}:")
    for class_name in all_classes[split]:
        class_path = os.path.join(dataset_dir, split, class_name)
        images = [f for f in os.listdir(class_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))][:3]
        for img_name in images:
            img_path = os.path.join(class_path, img_name)
            with Image.open(img_path) as img:
                print(f"  {class_name} - {img_name}: {img.size}")
