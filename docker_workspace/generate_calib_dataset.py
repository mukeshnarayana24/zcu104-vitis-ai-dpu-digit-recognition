import os
import cv2
import numpy as np
from tensorflow.keras.datasets import mnist

# Load MNIST test set (for evaluation)
_, (x_test, y_test) = mnist.load_data()

# Create folder for test images
os.makedirs("calib_images", exist_ok=True)

# Open label file
with open("labels.txt", "w") as label_file:
    for i in range(100):
        img = x_test[i]
        label = y_test[i]
        
        # Save image
        image_path = f"calib_images/img_{i:05d}.png"
        cv2.imwrite(image_path, img)
        
        # Write label to text file
        #label_file.write(f"{label}\n")

print("✅ Saved 100 test images in 'calib_images/' and labels in 'labels.txt'")
