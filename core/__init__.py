"""
Module core pour l'indexation et la recherche sémantique de médias avec CLIP.
"""

from .clip_utils import CLIPEmbedder, get_embedder
from .indexer import extract_and_index, save_index_backup, restore_index_backup
from .searcher import search_by_text
from .captioner import BLIPCaptioner, get_captioner
from .reranker import CrossEncoderReranker, get_reranker

__all__ = [
    'CLIPEmbedder', 
    'get_embedder', 
    'extract_and_index', 
    'search_by_text',
    'save_index_backup',
    'restore_index_backup',
    'BLIPCaptioner',
    'get_captioner',
    'CrossEncoderReranker',
    'get_reranker'
]

