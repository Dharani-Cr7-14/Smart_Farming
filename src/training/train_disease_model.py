# train_disease_model.py
import sys
import os

# Add src/ to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipelines.load_disease_dataset import load_disease_dataset
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Load dataset
print("Loading dataset...")
train_generator, val_generator, test_generator, class_indices = load_disease_dataset()
num_classes = len(class_indices)
print(f"Number of classes: {num_classes}")

# Build ResNet50 model
print("Building model...")
base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224,224,3))
base_model.trainable = False  # freeze base

x = GlobalAveragePooling2D()(base_model.output)
x = Dense(128, activation='relu')(x)
output = Dense(num_classes, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=output)

# Compile model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
print("Model compiled successfully.")

# Callbacks
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
checkpoint = ModelCheckpoint('models/plant_disease_model.h5', monitor='val_loss', save_best_only=True)

# Train model
print("Starting training...")
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=20,  # increase if GPU allows
    callbacks=[early_stop, checkpoint]
)

# Evaluate
test_loss, test_acc = model.evaluate(test_generator)
print("Test Accuracy:", test_acc)
