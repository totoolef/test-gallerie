# Création des Icônes PWA

Pour créer les icônes nécessaires pour l'application PWA, vous avez plusieurs options :

## Option 1 : Utiliser un générateur en ligne

1. Allez sur https://www.pwabuilder.com/imageGenerator
2. Uploadez une image (512x512px recommandé)
3. Téléchargez les icônes générées
4. Placez-les dans le dossier `public/` :
   - `icon-192.png` (192x192px)
   - `icon-512.png` (512x512px)

## Option 2 : Créer manuellement

1. Créez une image carrée (512x512px) avec votre logo/icône
2. Utilisez un outil comme ImageMagick ou un éditeur d'images pour redimensionner :
   ```bash
   # Avec ImageMagick
   convert icon.png -resize 192x192 public/icon-192.png
   convert icon.png -resize 512x512 public/icon-512.png
   ```

## Option 3 : Utiliser Python (Pillow)

Créez un script `create_icons.py` :

```python
from PIL import Image
import os

# Créer une icône simple si vous n'avez pas d'image
def create_simple_icon():
    # Créer une image bleue avec un "M"
    img = Image.new('RGB', (512, 512), color='#007AFF')
    # Ici vous pouvez ajouter du texte ou une image
    return img

# Redimensionner
sizes = [192, 512]
for size in sizes:
    img = create_simple_icon()
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    img.save(f'public/icon-{size}.png')
    print(f'✅ Créé: public/icon-{size}.png')
```

## Icônes temporaires

En attendant, vous pouvez utiliser des icônes temporaires ou créer des fichiers PNG simples avec un fond bleu.

