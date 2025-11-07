"""
Module de filtrage pour préfiltrer la recherche avant FAISS.
Permet de filtrer par type de média, date, dossier, etc.
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
from pathlib import Path


def filter_metadata(metadata: List[Dict],
                    media_type: Optional[str] = None,
                    date_range: Optional[Tuple[date, date]] = None,
                    include_dirs: Optional[List[str]] = None,
                    exclude_dirs: Optional[List[str]] = None) -> List[int]:
    """
    Filtre les métadonnées selon les critères spécifiés et retourne les indices admissibles.
    
    Args:
        metadata: Liste de dictionnaires de métadonnées
        media_type: Type de média à inclure ('image', 'video', ou None pour tous)
        date_range: Tuple (date_debut, date_fin) pour filtrer par date (si disponible dans metadata)
        include_dirs: Liste de dossiers à inclure (chemins absolus ou relatifs)
        exclude_dirs: Liste de dossiers à exclure (chemins absolus ou relatifs)
        
    Returns:
        Liste d'indices admissibles (pour sous-chercher dans FAISS ou post-filtrer)
    """
    admissible_indices = []
    
    for idx, meta in enumerate(metadata):
        # Filtre par type de média
        if media_type is not None:
            meta_type = meta.get("media_type", "")
            if meta_type != media_type:
                continue
        
        # Filtre par date (si disponible dans metadata)
        if date_range is not None:
            meta_date = meta.get("date", None)
            if meta_date:
                try:
                    # Parser la date (format ISO ou autre)
                    if isinstance(meta_date, str):
                        meta_date_obj = datetime.fromisoformat(meta_date).date()
                    elif isinstance(meta_date, datetime):
                        meta_date_obj = meta_date.date()
                    elif isinstance(meta_date, date):
                        meta_date_obj = meta_date
                    else:
                        meta_date_obj = None
                    
                    if meta_date_obj:
                        date_start, date_end = date_range
                        if not (date_start <= meta_date_obj <= date_end):
                            continue
                except Exception:
                    # Si erreur de parsing, inclure par défaut
                    pass
        
        # Filtre par dossier (include_dirs)
        if include_dirs is not None and len(include_dirs) > 0:
            file_path = meta.get("file_path", "")
            if not file_path:
                continue
            
            # Normaliser les chemins
            file_path_abs = os.path.abspath(file_path)
            included = False
            
            for include_dir in include_dirs:
                include_dir_abs = os.path.abspath(include_dir)
                # Vérifier si le fichier est dans ce dossier
                try:
                    if os.path.commonpath([file_path_abs, include_dir_abs]) == include_dir_abs:
                        included = True
                        break
                except ValueError:
                    # Chemins non compatibles, continuer
                    pass
            
            if not included:
                continue
        
        # Filtre par dossier (exclude_dirs)
        if exclude_dirs is not None and len(exclude_dirs) > 0:
            file_path = meta.get("file_path", "")
            if file_path:
                file_path_abs = os.path.abspath(file_path)
                excluded = False
                
                for exclude_dir in exclude_dirs:
                    exclude_dir_abs = os.path.abspath(exclude_dir)
                    # Vérifier si le fichier est dans ce dossier
                    try:
                        if os.path.commonpath([file_path_abs, exclude_dir_abs]) == exclude_dir_abs:
                            excluded = True
                            break
                    except ValueError:
                        # Chemins non compatibles, continuer
                        pass
                
                if excluded:
                    continue
        
        # Si tous les filtres passent, ajouter l'indice
        admissible_indices.append(idx)
    
    return admissible_indices


def get_unique_dirs(metadata: List[Dict]) -> List[str]:
    """
    Extrait la liste unique des dossiers contenant les médias.
    
    Args:
        metadata: Liste de dictionnaires de métadonnées
        
    Returns:
        Liste de chemins de dossiers uniques (triés)
    """
    dirs = set()
    
    for meta in metadata:
        file_path = meta.get("file_path", "")
        if file_path:
            try:
                dir_path = os.path.dirname(os.path.abspath(file_path))
                if dir_path:
                    dirs.add(dir_path)
            except Exception:
                pass
    
    return sorted(list(dirs))


def get_media_types(metadata: List[Dict]) -> List[str]:
    """
    Extrait la liste unique des types de médias.
    
    Args:
        metadata: Liste de dictionnaires de métadonnées
        
    Returns:
        Liste de types de médias uniques
    """
    types = set()
    
    for meta in metadata:
        media_type = meta.get("media_type", "")
        if media_type:
            types.add(media_type)
    
    return sorted(list(types))


def extract_date_from_metadata(metadata: List[Dict]) -> Optional[Tuple[date, date]]:
    """
    Extrait la plage de dates disponible dans les métadonnées.
    
    Args:
        metadata: Liste de dictionnaires de métadonnées
        
    Returns:
        Tuple (date_min, date_max) ou None si aucune date disponible
    """
    dates = []
    
    for meta in metadata:
        meta_date = meta.get("date", None)
        if meta_date:
            try:
                if isinstance(meta_date, str):
                    meta_date_obj = datetime.fromisoformat(meta_date).date()
                elif isinstance(meta_date, datetime):
                    meta_date_obj = meta_date.date()
                elif isinstance(meta_date, date):
                    meta_date_obj = meta_date
                else:
                    continue
                
                dates.append(meta_date_obj)
            except Exception:
                pass
    
    if not dates:
        return None
    
    return (min(dates), max(dates))

