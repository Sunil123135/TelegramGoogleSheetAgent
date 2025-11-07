#!/usr/bin/env python3
"""
Generate placeholder icons for the RAG Highlighter Chrome extension.
Run this script to create icon16.png, icon48.png, and icon128.png
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not found. Installing Pillow...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pillow'])
    from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    """Create a simple gradient icon with a magnifying glass symbol"""
    
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient effect with circles
    for i in range(10):
        opacity = int(255 * (1 - i / 10))
        color = f'#{hex(102 + i * 8)[2:].zfill(2)}{hex(126 + i * 8)[2:].zfill(2)}{hex(234)[2:]}'
        
    # Draw a simple magnifying glass
    center_x, center_y = size // 2, size // 2
    glass_radius = int(size * 0.25)
    
    # Glass circle (white with border)
    draw.ellipse(
        [center_x - glass_radius, center_y - glass_radius,
         center_x + glass_radius, center_y + glass_radius],
        outline='white',
        width=max(2, size // 32)
    )
    
    # Handle
    handle_start_x = center_x + int(glass_radius * 0.7)
    handle_start_y = center_y + int(glass_radius * 0.7)
    handle_end_x = center_x + int(glass_radius * 1.5)
    handle_end_y = center_y + int(glass_radius * 1.5)
    
    draw.line(
        [handle_start_x, handle_start_y, handle_end_x, handle_end_y],
        fill='white',
        width=max(2, size // 32)
    )
    
    # Save
    img.save(f'icons/{filename}')
    print(f'✓ Created icons/{filename} ({size}x{size})')

def main():
    print('Generating RAG Highlighter icons...')
    create_icon(16, 'icon16.png')
    create_icon(48, 'icon48.png')
    create_icon(128, 'icon128.png')
    print('\n✓ All icons generated successfully!')
    print('Icons are in chrome_ext/icons/')

if __name__ == '__main__':
    main()

