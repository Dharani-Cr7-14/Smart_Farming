import os
import sys
import numpy as np
import tensorflow as tf
from pathlib import Path
from sklearn.utils.class_weight import compute_class_weight

# Add src to python path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

def get_generators(batch_size=32, img_size=(224, 224)):
    base_dir = os.path.join(ROOT_DIR, "data", "plant_disease")
    train_dir = os.path.join(base_dir, "train")
    val_dir = os.path.join(base_dir, "val")
    
    # 1. ImageDataGenerators using preprocess_input (No 1/255 rescaling)
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    val_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
    
    train_generator = train_datagen.flow_from_directory(
        train_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical'
    )
    
    val_generator = val_datagen.flow_from_directory(
        val_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical'
    )
    
    return train_generator, val_generator

def build_model(num_classes):
    print("Building ResNet50 Transfer Learning model...")
    base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    
    # Freeze the base initially
    base_model.trainable = False
    
    x = GlobalAveragePooling2D()(base_model.output)
    x = Dense(128, activation='relu')(x)
    output = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=output)
    return model, base_model

def run_fine_tuning(dry_run=False):
    print("="*60)
    print("🌱 SMART FARMING DECISION SUPPORT SYSTEM - CNN TWO-STAGE FINE-TUNING PIPELINE")
    print("="*60)
    
    # Load generators
    train_generator, val_generator = get_generators()
    num_classes = len(train_generator.class_indices)
    
    # Calculate class weights
    print("\nCalculating balanced class weights...")
    classes = train_generator.classes
    unique_classes = np.unique(classes)
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=unique_classes,
        y=classes
    )
    class_weight_dict = {int(i): float(w) for i, w in zip(unique_classes, class_weights)}
    
    print("\nClass weights mapping:")
    inverse_class_indices = {v: k for k, v in train_generator.class_indices.items()}
    for i, w in class_weight_dict.items():
        print(f"  Class {i:2d} ({inverse_class_indices[i]:50s}): Weight = {w:.4f}")
        
    model, base_model = build_model(num_classes)
    
    # --- STAGE 1 CONFIGURATION ---
    print("\n" + "-"*50)
    print("STAGE 1: Training Classification Head")
    print("-"*50)
    print("Base ResNet50: Frozen")
    print("Learning Rate: 1e-3")
    print("Epochs: 5")
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    stage1_checkpoint = os.path.join(ROOT_DIR, "models", "plant_disease_stage1_best.h5")
    stage1_callbacks = [
        ModelCheckpoint(stage1_checkpoint, monitor='val_loss', save_best_only=True, save_weights_only=False)
    ]
    
    # --- STAGE 2 CONFIGURATION ---
    print("\n" + "-"*50)
    print("STAGE 2: Unfreezing & Fine-Tuning Upper Layers")
    print("-"*50)
    print("Unfreezing last 15 layers of ResNet50 base (excluding BatchNormalization)...")
    
    # Unfreeze only the last 15 layers of the base
    base_model.trainable = True
    for layer in base_model.layers[:-15]:
        layer.trainable = False
        
    # Keep BatchNormalization layers frozen
    for layer in base_model.layers[-15:]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
            
    print("Stage 2 learning rate: 1e-5")
    print("Maximum epochs: 15")
    
    stage2_checkpoint = os.path.join(ROOT_DIR, "models", "plant_disease_finetuned_best.h5")
    stage2_callbacks = [
        EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True),
        ModelCheckpoint(stage2_checkpoint, monitor='val_loss', save_best_only=True, save_weights_only=False)
    ]
    
    if dry_run:
        print("\n✅ Dry-run check completed successfully. Exiting without training.")
        return
        
    # --- RUN TRAINING (IF NOT DRY RUN) ---
    stage1_checkpoint = os.path.join(ROOT_DIR, "models", "plant_disease_stage1_best.h5")
    run_stage1 = True
    if os.path.exists(stage1_checkpoint):
        print(f"\n💡 Found existing Stage 1 checkpoint at: {stage1_checkpoint}")
        print("Bypassing Stage 1 training and proceeding directly to Stage 2.")
        run_stage1 = False

    if run_stage1:
        print("\nStarting Stage 1 training...")
        model.fit(
            train_generator,
            validation_data=val_generator,
            epochs=5,
            class_weight=class_weight_dict,
            callbacks=stage1_callbacks
        )
        print(f"\nStage 1 completed. Saved best weights to: {stage1_checkpoint}")
    
    # Resolve tensorflow-metal remapper graph mutation bug by clearing session and rebuilding clean model
    print("\nRebuilding clean model instance for Stage 2...")
    tf.keras.backend.clear_session()
    model, base_model = build_model(num_classes)
    
    # Apply Stage 2 frozen/unfrozen configuration on clean model layers
    base_model.trainable = True
    for layer in base_model.layers[:-15]:
        layer.trainable = False
    for layer in base_model.layers[-15:]:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
            
    print(f"Loading Stage 1 checkpoint weights into Stage 2 model: {stage1_checkpoint}")
    model.load_weights(stage1_checkpoint)
    
    # Re-compile clean Stage 2 model freshly
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("\nStarting Stage 2 fine-tuning...")
    model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=15,
        class_weight=class_weight_dict,
        callbacks=stage2_callbacks
    )
    print("\n🎉 CNN Two-Stage Fine-Tuning completed successfully!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run dry run verification checks without training")
    args = parser.parse_args()
    
    run_fine_tuning(dry_run=args.dry_run)
