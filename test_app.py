#!/usr/bin/env python
"""
Script de test pour vérifier que l'application fonctionne correctement.
"""

import os
import sys

# Fix pour OpenMP sur macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
torch.set_num_threads(1)

def test_imports():
    """Test que tous les imports fonctionnent."""
    print("🔍 Test des imports...")
    try:
        from core.indexer import extract_and_index_multiple_dirs, get_media_files
        print("  ✅ core.indexer")
    except Exception as e:
        print(f"  ❌ core.indexer: {e}")
        return False
    
    try:
        from core.searcher import load_index_and_metadata, search
        print("  ✅ core.searcher")
    except Exception as e:
        print(f"  ❌ core.searcher: {e}")
        return False
    
    try:
        from core.clip_utils import get_embedder, CLIPEmbedder
        print("  ✅ core.clip_utils")
    except Exception as e:
        print(f"  ❌ core.clip_utils: {e}")
        return False
    
    try:
        from core.captioner import get_captioner, BLIPCaptioner
        print("  ✅ core.captioner")
    except Exception as e:
        print(f"  ❌ core.captioner: {e}")
        return False
    
    try:
        from core.reranker import get_reranker, CrossEncoderReranker
        print("  ✅ core.reranker")
    except Exception as e:
        print(f"  ❌ core.reranker: {e}")
        return False
    
    try:
        from photos_utils import get_photos_from_photos_app, get_photos_from_library
        print("  ✅ photos_utils")
    except Exception as e:
        print(f"  ❌ photos_utils: {e}")
        return False
    
    try:
        from ui_utils import make_thumbnail, get_video_preview, open_in_finder, human_readable_score, format_file_size
        print("  ✅ ui_utils")
    except Exception as e:
        print(f"  ❌ ui_utils: {e}")
        return False
    
    try:
        import streamlit as st
        print("  ✅ streamlit")
    except Exception as e:
        print(f"  ❌ streamlit: {e}")
        return False
    
    return True


def test_basic_functions():
    """Test des fonctions de base."""
    print("\n🔍 Test des fonctions de base...")
    
    try:
        from core.indexer import get_media_files
        if os.path.exists('data'):
            images, videos = get_media_files('data')
            print(f"  ✅ get_media_files: {len(images)} images, {len(videos)} vidéos")
        else:
            print("  ⚠️  Dossier data/ non trouvé (normal si vide)")
    except Exception as e:
        print(f"  ❌ get_media_files: {e}")
        return False
    
    try:
        from ui_utils import human_readable_score, format_file_size
        score = human_readable_score(0.85)
        size = format_file_size(1024 * 1024)
        print(f"  ✅ UI utils: score={score}, size={size}")
    except Exception as e:
        print(f"  ❌ UI utils: {e}")
        return False
    
    return True


def test_index_loading():
    """Test du chargement de l'index."""
    print("\n🔍 Test du chargement de l'index...")
    
    try:
        from core.searcher import load_index_and_metadata
        if os.path.exists('index.faiss') and os.path.exists('metadata.json'):
            index, metadata = load_index_and_metadata('index.faiss', 'metadata.json')
            print(f"  ✅ Index chargé: {index.ntotal} embeddings, {len(metadata)} métadonnées")
        else:
            print("  ⚠️  Index non trouvé (normal si pas encore créé)")
    except Exception as e:
        print(f"  ❌ Chargement index: {e}")
        return False
    
    return True


def test_app_simple_import():
    """Test que app_simple.py peut être importé."""
    print("\n🔍 Test de l'import de app_simple.py...")
    
    try:
        # On ne peut pas vraiment importer app_simple.py car il lance Streamlit
        # Mais on peut vérifier la syntaxe
        import py_compile
        py_compile.compile('app_simple.py', doraise=True)
        print("  ✅ Syntaxe de app_simple.py valide")
    except py_compile.PyCompileError as e:
        print(f"  ❌ Erreur de syntaxe dans app_simple.py: {e}")
        return False
    except Exception as e:
        print(f"  ⚠️  Erreur lors de la compilation: {e}")
        return False
    
    return True


def main():
    """Fonction principale de test."""
    print("=" * 60)
    print("🧪 Tests de l'application")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Fonctions de base
    results.append(("Fonctions de base", test_basic_functions()))
    
    # Test 3: Chargement de l'index
    results.append(("Chargement de l'index", test_index_loading()))
    
    # Test 4: Syntaxe de app_simple.py
    results.append(("Syntaxe app_simple.py", test_app_simple_import()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 Résumé des tests")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ Tous les tests sont passés avec succès!")
        return 0
    else:
        print("❌ Certains tests ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(main())

