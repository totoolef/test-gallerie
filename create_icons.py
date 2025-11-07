"""
Script pour créer les icônes PWA nécessaires.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=512):
    """Crée une icône simple avec un fond bleu et un 'M'."""
    # Créer une image avec fond bleu Apple
    img = Image.new('RGB', (size, size), color='#007AFF')
    draw = ImageDraw.Draw(img)
    
    # Dessiner un 'M' blanc au centre
    try:
        # Essayer d'utiliser une police système
        font_size = int(size * 0.4)
        try:
            # macOS
            font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', font_size)
        except:
            try:
                # Linux
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
            except:
                # Fallback sur police par défaut
                font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Calculer la position du texte pour le centrer
    text = "M"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]
    
    draw.text((x, y), text, fill='white', font=font)
    
    return img

def main():
    """Génère les icônes nécessaires."""
    # Créer le dossier public s'il n'existe pas
    public_dir = Path('public')
    public_dir.mkdir(exist_ok=True)
    
    # Tailles nécessaires
    sizes = [192, 512]
    
    for size in sizes:
        icon = create_icon(size)
        icon_path = public_dir / f'icon-{size}.png'
        icon.save(icon_path)
        print(f'✅ Créé: {icon_path} ({size}x{size}px)')
    
    print('\n✅ Toutes les icônes ont été créées!')

if __name__ == '__main__':
    from pathlib import Path
    main()

