# load_disease_dataset.py
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import json
import os

def load_disease_dataset(batch_size=32, img_size=(224,224)):
    """
    Loads the plant disease dataset from data/plant_disease
    and returns train, val, test generators and class indices.
    """

    # Paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'plant_disease'))
    train_dir = os.path.join(base_dir, 'train')
    val_dir = os.path.join(base_dir, 'val')
    test_dir = os.path.join(base_dir, 'test')
    class_indices_path = os.path.join(base_dir, 'class_indices.json')

    # Data generators
    train_datagen = ImageDataGenerator(rescale=1./255,
                                       rotation_range=20,
                                       width_shift_range=0.2,
                                       height_shift_range=0.2,
                                       shear_range=0.2,
                                       zoom_range=0.2,
                                       horizontal_flip=True,
                                       fill_mode='nearest')

    val_datagen = ImageDataGenerator(rescale=1./255)
    test_datagen = ImageDataGenerator(rescale=1./255)

    # Flow from directory
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

    test_generator = test_datagen.flow_from_directory(
        test_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical'
    )

    # Save class indices
    class_indices = train_generator.class_indices
    with open(class_indices_path, 'w') as f:
        json.dump(class_indices, f)

    return train_generator, val_generator, test_generator, class_indices

# Example usage
if __name__ == "__main__":
    train_gen, val_gen, test_gen, classes = load_disease_dataset()
    print("Classes:", classes)
