#The part that posts images one by one to the api and saves the corresponding response jsons in bulk from local in local.
import os
import requests
import json

# Configure input and output directories
input_dir = "input_img/trial_1"  # Replace with the directory containing .tif files
output_dir = "input_img/trial_1/responses"   # Replace with the directory to save JSON responses
os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist

# API details
api_url = "https://solarquote.api.abacus.ai/api/predictWithBinaryData"
deployment_token = "4f8ad7e922ec4c0aaf0661c0c32292b8"  # Replace with your token
deployment_id = "ec5487e60"  # Replace with your deployment ID

# Process all .tif files in the directory
for tif_file in os.listdir(input_dir):
    if tif_file.endswith(".tif"):
        try:
            # Full path to the .tif file
            file_path = os.path.join(input_dir, tif_file)
            
            # POST request
            with open(file_path, "rb") as file_data:
                # Let requests handle Content-Type and boundaries automatically
                response = requests.post(
                    f"{api_url}?deploymentToken={deployment_token}&deploymentId={deployment_id}",
                    files={"blob": file_data},
                )
            
            # Check the response status
            if response.status_code == 200:
                # Parse JSON response
                response_json = response.json()
                
                # Save the response to a JSON file
                output_file = os.path.join(output_dir, f"{os.path.splitext(tif_file)[0]}.json")
                with open(output_file, "w") as json_file:
                    json.dump(response_json, json_file, indent=4)
                print(f"Response saved for {tif_file}: {output_file}")
            else:
                print(f"Failed for {tif_file}: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"Error processing {tif_file}: {e}")


#The part that takes the unit8 imagearray values visualizes them into masks on the scale of image and 
# saves thse masks as png from local in local.
import os
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label
import random

# Set the input and output directories
json_dir = "input_img/trial_1/responses"  # Directory containing the JSON files
output_dir = "input_img/trial_1"  # Directory to save the images
os.makedirs(output_dir, exist_ok=True)  # Create the output directory if it doesn't exist

# Target dimensions for the output images
output_size = (598, 599)

def generate_colormap(num_components):
    """Generate a colormap for the connected components."""
    colormap = np.zeros((num_components + 1, 3), dtype=np.uint8)  # +1 for background
    for i in range(1, num_components + 1):  # Skip background
        colormap[i] = [random.randint(0, 255) for _ in range(3)]
    return colormap

# Process each JSON file in the directory
for json_file in os.listdir(json_dir):
    if json_file.endswith(".json"):  # Ensure it's a JSON file
        json_path = os.path.join(json_dir, json_file)
        try:
            # Read the JSON file
            with open(json_path, "r") as file:
                response = json.load(file)
            
            # Check if the response is successful and contains 'image_array'
            if response.get("success") and "result" in response and "image_array" in response["result"]:
                image_array = response["result"]["image_array"]
                
                # Convert the array into a numpy array
                binary_mask = np.array(image_array, dtype=np.uint8)
                
                # Identify connected components
                labeled_array, num_components = label(binary_mask)
                
                # Generate a colormap for the connected components
                colormap = generate_colormap(num_components)
                
                # Map labeled components to colors
                color_image = colormap[labeled_array]
                
                # Convert to PIL Image and resize
                image = Image.fromarray(color_image, mode="RGB")
                image = image.resize(output_size, Image.NEAREST)
                
                # Save the image
                output_path = os.path.join(output_dir, f"{os.path.splitext(json_file)[0]}_connected.png")
                image.save(output_path)
                print(f"Saved connected component image: {output_path}")
            else:
                print(f"Skipping {json_file}: Invalid or unsuccessful response")
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

