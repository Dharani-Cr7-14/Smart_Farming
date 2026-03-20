from tkinter import Tk
from tkinter.filedialog import askopenfilename
import tensorflow as tf
import numpy as np
import json
import os
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt

# Load model
model_path = os.path.join("models", "plant_disease_model.h5")
model = tf.keras.models.load_model(model_path)

# Load class indices
with open("class_indices.json", "r") as f:
    class_indices = json.load(f)
idx_to_class = {v: k for k, v in class_indices.items()}

def predict_disease(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    preds = model.predict(img_array)[0]
    top_indices = preds.argsort()[-3:][::-1]
    top_predictions = [(idx_to_class[i], preds[i]*100) for i in top_indices]
    return top_predictions, img

if __name__ == "__main__":
    # Initialize Tkinter properly
    root = Tk()
    root.withdraw()           # Hide the main Tkinter window
    root.attributes("-topmost", True)  # Bring file dialog to front

    print("Select a leaf image...")
    test_img = askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])

    root.destroy()  # Close Tkinter properly

    if test_img:
        top_preds, img = predict_disease(test_img)
        print("\nTop Predictions:")
        for disease, conf in top_preds:
            print(f"{disease}: {conf:.2f}% confidence")

        plt.imshow(img)
        plt.axis('off')
        plt.title("Predicted: " + top_preds[0][0])
        plt.show()
    else:
        print("⚠️ No image selected.")
