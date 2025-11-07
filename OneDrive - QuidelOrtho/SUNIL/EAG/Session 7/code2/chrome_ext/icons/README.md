# Icon Files

Place your extension icon files here:
- `icon16.png` - 16x16 pixels
- `icon48.png` - 48x48 pixels
- `icon128.png` - 128x128 pixels

## Quick Icon Generation

You can:
1. Use any PNG image editor
2. Or use an online icon generator
3. Or create simple colored squares as placeholders

## Placeholder Creation (Python)

```python
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    # Create gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw circle
    draw.ellipse([size//4, size//4, 3*size//4, 3*size//4], fill='#764ba2')
    
    # Save
    img.save(filename)

create_icon(16, 'icon16.png')
create_icon(48, 'icon48.png')
create_icon(128, 'icon128.png')
```

For now, the extension will work without icons (Chrome will show a default icon).

