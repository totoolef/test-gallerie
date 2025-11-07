"""
Module d'évaluation pour mesurer la performance du moteur de recherche.
Fournit des métriques comme hit@k, MRR, et des visualisations.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour Streamlit


def hit_at_k(results: List[Dict], expected_filename: str, k: int = 5) -> bool:
    """
    Vérifie si le fichier attendu est dans les k premiers résultats.
    
    Args:
        results: Liste de dictionnaires avec "path" et "score"
        expected_filename: Nom du fichier attendu (ou chemin)
        k: Nombre de résultats à considérer (défaut: 5)
        
    Returns:
        True si trouvé dans les k premiers, False sinon
    """
    if not results:
        return False
    
    # Limiter aux k premiers
    top_k = results[:k]
    
    for result in top_k:
        file_path = result.get("path", "")
        if not file_path:
            continue
        
        # Vérifier si le nom de fichier correspond
        import os
        filename = os.path.basename(file_path)
        if filename == expected_filename or file_path.endswith(expected_filename):
            return True
    
    return False


def get_rank(results: List[Dict], expected_filename: str) -> Optional[int]:
    """
    Trouve le rang du fichier attendu dans les résultats.
    
    Args:
        results: Liste de dictionnaires avec "path" et "score"
        expected_filename: Nom du fichier attendu
        
    Returns:
        Rang (1-based) ou None si non trouvé
    """
    if not results:
        return None
    
    import os
    
    for rank, result in enumerate(results, 1):
        file_path = result.get("path", "")
        if not file_path:
            continue
        
        filename = os.path.basename(file_path)
        if filename == expected_filename or file_path.endswith(expected_filename):
            return rank
    
    return None


def mean_reciprocal_rank(list_of_rankings: List[Optional[int]]) -> float:
    """
    Calcule le Mean Reciprocal Rank (MRR).
    
    Args:
        list_of_rankings: Liste de rangs (1-based) ou None si non trouvé
        
    Returns:
        MRR (0.0 à 1.0)
    """
    if not list_of_rankings:
        return 0.0
    
    reciprocal_ranks = []
    
    for rank in list_of_rankings:
        if rank is not None and rank > 0:
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
    
    if not reciprocal_ranks:
        return 0.0
    
    return float(np.mean(reciprocal_ranks))


def hit_at_k_multiple(list_of_results: List[List[Dict]], 
                      list_of_expected: List[str], 
                      k: int = 5) -> float:
    """
    Calcule le taux de hit@k sur plusieurs requêtes.
    
    Args:
        list_of_results: Liste de listes de résultats (une par requête)
        list_of_expected: Liste de noms de fichiers attendus (une par requête)
        k: Nombre de résultats à considérer (défaut: 5)
        
    Returns:
        Taux de hit@k (0.0 à 1.0)
    """
    if len(list_of_results) != len(list_of_expected):
        raise ValueError("Les listes de résultats et d'attendus doivent avoir la même longueur")
    
    if not list_of_results:
        return 0.0
    
    hits = 0
    
    for results, expected in zip(list_of_results, list_of_expected):
        if hit_at_k(results, expected, k):
            hits += 1
    
    return hits / len(list_of_results)


def score_distribution_plot(scores: List[float], 
                            title: str = "Distribution des scores de similarité",
                            bins: int = 20) -> plt.Figure:
    """
    Crée un histogramme de la distribution des scores.
    
    Args:
        scores: Liste de scores de similarité
        title: Titre du graphique (défaut: "Distribution des scores de similarité")
        bins: Nombre de bins pour l'histogramme (défaut: 20)
        
    Returns:
        Figure matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if not scores:
        ax.text(0.5, 0.5, "Aucun score disponible", 
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title(title)
        return fig
    
    # Créer l'histogramme
    ax.hist(scores, bins=bins, edgecolor='black', alpha=0.7)
    ax.set_xlabel("Score de similarité")
    ax.set_ylabel("Fréquence")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    # Ajouter des statistiques
    mean_score = np.mean(scores)
    median_score = np.median(scores)
    std_score = np.std(scores)
    
    stats_text = f"Moyenne: {mean_score:.3f}\nMédiane: {median_score:.3f}\nÉcart-type: {std_score:.3f}"
    ax.text(0.02, 0.98, stats_text, 
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    return fig


def precision_at_k(results: List[Dict], expected_filename: str, k: int = 5) -> float:
    """
    Calcule la précision à k (pour une seule requête, c'est 1 si trouvé, 0 sinon).
    
    Args:
        results: Liste de dictionnaires avec "path" et "score"
        expected_filename: Nom du fichier attendu
        k: Nombre de résultats à considérer (défaut: 5)
        
    Returns:
        Précision à k (0.0 ou 1.0)
    """
    return 1.0 if hit_at_k(results, expected_filename, k) else 0.0


def recall_at_k(results: List[Dict], expected_filename: str, k: int = 5) -> float:
    """
    Calcule le rappel à k (pour une seule requête, c'est 1 si trouvé, 0 sinon).
    
    Args:
        results: Liste de dictionnaires avec "path" et "score"
        expected_filename: Nom du fichier attendu
        k: Nombre de résultats à considérer (défaut: 5)
        
    Returns:
        Rappel à k (0.0 ou 1.0)
    """
    return 1.0 if hit_at_k(results, expected_filename, k) else 0.0


def evaluate_search_results(test_queries: List[Dict],
                             search_function,
                             top_k: int = 5) -> Dict:
    """
    Évalue les résultats de recherche sur un ensemble de requêtes de test.
    
    Args:
        test_queries: Liste de dictionnaires avec "query" et "expected_filename"
        search_function: Fonction de recherche qui prend (query, ...) et retourne List[Dict]
        top_k: Nombre de résultats à considérer (défaut: 5)
        
    Returns:
        Dictionnaire avec les métriques d'évaluation
    """
    results_by_query = []
    ranks = []
    scores_all = []
    
    for test_case in test_queries:
        query = test_case.get("query", "")
        expected_filename = test_case.get("expected_filename", "")
        
        if not query or not expected_filename:
            continue
        
        try:
            # Effectuer la recherche
            results = search_function(query)
            
            # Extraire les scores
            scores = [r.get("score", 0.0) for r in results]
            scores_all.extend(scores)
            
            # Trouver le rang
            rank = get_rank(results, expected_filename)
            ranks.append(rank)
            
            results_by_query.append({
                "query": query,
                "expected": expected_filename,
                "results": results,
                "rank": rank,
                "found": rank is not None
            })
        except Exception as e:
            # En cas d'erreur, considérer comme non trouvé
            ranks.append(None)
            results_by_query.append({
                "query": query,
                "expected": expected_filename,
                "results": [],
                "rank": None,
                "found": False,
                "error": str(e)
            })
    
    # Calculer les métriques
    hit_at_1 = hit_at_k_multiple([r["results"] for r in results_by_query],
                                  [r["expected"] for r in results_by_query],
                                  k=1)
    hit_at_5 = hit_at_k_multiple([r["results"] for r in results_by_query],
                                  [r["expected"] for r in results_by_query],
                                  k=5)
    hit_at_10 = hit_at_k_multiple([r["results"] for r in results_by_query],
                                   [r["expected"] for r in results_by_query],
                                   k=10)
    
    mrr = mean_reciprocal_rank(ranks)
    
    return {
        "hit_at_1": hit_at_1,
        "hit_at_5": hit_at_5,
        "hit_at_10": hit_at_10,
        "mrr": mrr,
        "total_queries": len(test_queries),
        "found_count": sum(1 for r in ranks if r is not None),
        "not_found_count": sum(1 for r in ranks if r is None),
        "results_by_query": results_by_query,
        "all_scores": scores_all
    }

