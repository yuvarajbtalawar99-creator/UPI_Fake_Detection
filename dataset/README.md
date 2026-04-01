# Screenshot Classification Dataset

Add your labeled payment screenshots to these folders for training the KAVACH Deep Learning model.

## Folders
- `real/`: Put genuine screenshots from apps like PhonePe, GPay, Paytm, etc.
- `fake/`: Put edited, manipulated, or simulated screenshots that should be flagged.

## Requirements
- Aim for at least 50-100 images per folder for decent results.
- Images can be in PNG, JPG, or JPEG format.
- The training script will automatically resize them to 224x224.

## Training
Once you have added the images, run the following command from the root directory:
```bash
python train_screenshot_model.py
```
This will generate `screenshot_model.h5` in the root folder, which the backend will use automatically.
