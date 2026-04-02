import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    img = Image.new('RGB', (size, size), color='#0a0e27')
    draw = ImageDraw.Draw(img)
    # Draw a simple shield shape
    # Using simple polygon for shield
    w, h = size, size
    points = [
        (w * 0.2, h * 0.2), 
        (w * 0.8, h * 0.2), 
        (w * 0.8, h * 0.6), 
        (w * 0.5, h * 0.9), 
        (w * 0.2, h * 0.6)
    ]
    draw.polygon(points, fill='#0dc8f2')
    
    # Text K in the middle
    # Try to load a generic font (default if not found)
    # We will just write 'K'
    # Fallback default font is very small, so we might just draw lines for K
    
    # Creating fonts folder
    os.makedirs('frontend/icons', exist_ok=True)
    img.save(f'frontend/icons/{filename}')

create_icon(192, 'icon-192x192.png')
create_icon(512, 'icon-512x512.png')
print("Icons generated.")
