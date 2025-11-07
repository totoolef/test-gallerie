#!/usr/bin/env python
"""
Script d'évaluation automatique du moteur de recherche.
Teste l'efficacité du moteur sur un ensemble de requêtes connues.
"""

import os
# Fix pour OpenMP sur macOS - DOIT être au tout début
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
# Fix pour éviter les problèmes de threading avec FAISS/OpenMP
torch.set_num_threads(1)

import json
import argparse
import csv
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from core.searcher import search_by_text, load_index_and_metadata
from core.clip_utils import get_embedder
from core.eval import (
    hit_at_k, get_rank, mean_reciprocal_rank,
    hit_at_k_multiple, score_distribution_plot,
    evaluate_search_results
)


def load_test_queries(test_queries_path: str = "test_queries.json") -> List[Dict]:
    """
    Charge le fichier de requêtes de test.
    
    Args:
        test_queries_path: Chemin vers le fichier test_queries.json
        
    Returns:
        Liste de dictionnaires contenant "query" et "expected_filename"
    """
    if not os.path.exists(test_queries_path):
        print(f"❌ Fichier de test introuvable: {test_queries_path}")
        print(f"💡 Créez un fichier {test_queries_path} avec le format suivant:")
        print("""
[
  {
    "query": "une table en bois",
    "expected_filename": "table_1.jpg"
  },
  {
    "query": "personne sur un scooter",
    "expected_filename": "IMG_0412.png"
  }
]
        """)
        return []
    
    try:
        with open(test_queries_path, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        return queries
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {test_queries_path}: {e}")
        return []


def evaluate_search(test_queries_path: str = "test_queries.json",
                    index_path: str = "index.faiss",
                    metadata_path: str = "metadata.json",
                    top_k: int = 5,
                    model_name: str = "openai/clip-vit-large-patch14",
                    use_reranking: bool = True,
                    use_dynamic_threshold: bool = False,
                    fixed_threshold: float = 0.3,
                    always_rerank: bool = False,
                    rerank_if_below: float = None,
                    auto_translate: bool = False,
                    use_query_expansion: bool = True,
                    output_csv: str = None):
    """
    Évalue le moteur de recherche sur un ensemble de requêtes de test.
    
    Args:
        test_queries_path: Chemin vers le fichier de requêtes de test
        index_path: Chemin vers l'index FAISS
        metadata_path: Chemin vers les métadonnées
        top_k: Nombre de résultats à considérer pour chaque requête
        model_name: Nom du modèle CLIP
        use_reranking: Si True, active le rerank (déprécié, utiliser always_rerank ou rerank_if_below)
        use_dynamic_threshold: Si True, utilise un seuil dynamique
        fixed_threshold: Seuil fixe si use_dynamic_threshold=False
        always_rerank: Si True, applique toujours le rerank
        rerank_if_below: Si non-None et best_cosine < rerank_if_below, applique rerank
        auto_translate: Si True, traduit automatiquement la requête en anglais
        use_query_expansion: Si True, utilise la query expansion bilingue
        output_csv: Chemin vers le fichier CSV de sortie (optionnel)
    """
    print("="*80)
    print("📊 ÉVALUATION DU MOTEUR DE RECHERCHE")
    print("="*80)
    print()
    
    # Charger les requêtes de test
    queries = load_test_queries(test_queries_path)
    if not queries:
        return
    
    print(f"✅ {len(queries)} requête(s) de test chargée(s)")
    print()
    
    # Charger l'index et les métadonnées
    index, metadata = load_index_and_metadata(index_path, metadata_path)
    embedder = get_embedder(model_name=model_name)
    
    # Fonction de recherche wrapper
    def search_wrapper(query: str) -> List[Dict]:
        from core.searcher import search
        return search(
            query_text=query,
            index=index,
            metadata=metadata,
            embedder=embedder,
            top_k=top_k,
            use_query_expansion=use_query_expansion,
            auto_translate=auto_translate,
            use_dynamic_threshold=use_dynamic_threshold,
            fixed_threshold=fixed_threshold,
            always_rerank=always_rerank,
            rerank_if_below=rerank_if_below,
            use_captions=True
        )
    
    # Évaluer avec les nouvelles fonctions
    eval_results = evaluate_search_results(queries, search_wrapper, top_k=top_k)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("📊 RÉSULTATS DE L'ÉVALUATION")
    print("="*80)
    print()
    
    print(f"📈 Métriques globales:")
    print(f"   - Hit@1: {eval_results['hit_at_1']:.2%}")
    print(f"   - Hit@5: {eval_results['hit_at_5']:.2%}")
    print(f"   - Hit@10: {eval_results['hit_at_10']:.2%}")
    print(f"   - MRR (Mean Reciprocal Rank): {eval_results['mrr']:.4f}")
    print()
    
    print(f"📊 Statistiques:")
    print(f"   - Total requêtes: {eval_results['total_queries']}")
    print(f"   - Trouvées: {eval_results['found_count']}")
    print(f"   - Non trouvées: {eval_results['not_found_count']}")
    print()
    
    # Détails par requête
    print("📋 Détails par requête:")
    for result in eval_results['results_by_query']:
        status = "✅" if result["found"] else "❌"
        rank_info = f" (rang #{result['rank']})" if result["found"] else ""
        print(f"   {status} \"{result['query']}\" -> {result['expected']}{rank_info}")
    
    print()
    print("="*80)
    
    # Exporter CSV si demandé
    if output_csv:
        print(f"💾 Export des résultats vers {output_csv}...")
        try:
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Query", "Expected Filename", "Found", "Rank", "Top Hits", "Scores"])
                for result in eval_results['results_by_query']:
                    top_hits = [r.get("path", "") for r in result["results"][:5]]
                    scores = [f"{r.get('score', 0.0):.4f}" for r in result["results"][:5]]
                    writer.writerow([
                        result["query"],
                        result["expected"],
                        "Yes" if result["found"] else "No",
                        result["rank"] if result["found"] else "",
                        "; ".join(top_hits),
                        "; ".join(scores)
                    ])
            print(f"✅ Export CSV terminé: {output_csv}")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'export CSV: {e}")
    
    # Générer et sauvegarder l'histogramme si des scores sont disponibles
    if eval_results['all_scores']:
        try:
            import matplotlib
            matplotlib.use('Agg')
            fig = score_distribution_plot(eval_results['all_scores'])
            plot_path = output_csv.replace('.csv', '_scores.png') if output_csv else 'evaluation_scores.png'
            fig.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"📊 Histogramme sauvegardé: {plot_path}")
        except Exception as e:
            print(f"⚠️  Erreur lors de la génération de l'histogramme: {e}")


def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(
        description="Évaluer le moteur de recherche sur un ensemble de requêtes de test"
    )
    parser.add_argument(
        "--test-queries",
        type=str,
        default="test_queries.json",
        help="Chemin vers le fichier de requêtes de test (défaut: test_queries.json)"
    )
    parser.add_argument(
        "--index",
        type=str,
        default="index.faiss",
        help="Chemin vers l'index FAISS (défaut: index.faiss)"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="metadata.json",
        help="Chemin vers les métadonnées (défaut: metadata.json)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Nombre de résultats à considérer (défaut: 5)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai/clip-vit-large-patch14",
        help="Modèle CLIP à utiliser (défaut: openai/clip-vit-large-patch14)"
    )
    parser.add_argument(
        "--no-reranking",
        action="store_true",
        help="Désactiver le re-ranking"
    )
    parser.add_argument(
        "--dynamic-threshold",
        action="store_true",
        help="Utiliser un seuil dynamique"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Seuil fixe de similarité (défaut: 0.3)"
    )
    parser.add_argument(
        "--always-rerank",
        action="store_true",
        help="Appliquer toujours le rerank"
    )
    parser.add_argument(
        "--rerank-if-below",
        type=float,
        default=None,
        help="Appliquer rerank si best_cosine < seuil (défaut: None)"
    )
    parser.add_argument(
        "--auto-translate",
        action="store_true",
        help="Traduire automatiquement FR→EN"
    )
    parser.add_argument(
        "--no-query-expansion",
        action="store_true",
        help="Désactiver la query expansion"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=None,
        help="Chemin vers le fichier CSV de sortie (optionnel)"
    )
    
    args = parser.parse_args()
    
    evaluate_search(
        test_queries_path=args.test_queries,
        index_path=args.index,
        metadata_path=args.metadata,
        top_k=args.top_k,
        model_name=args.model,
        use_reranking=not args.no_reranking,
        use_dynamic_threshold=args.dynamic_threshold,
        fixed_threshold=args.threshold,
        always_rerank=args.always_rerank,
        rerank_if_below=args.rerank_if_below,
        auto_translate=args.auto_translate,
        use_query_expansion=not args.no_query_expansion,
        output_csv=args.output_csv
    )


# Appel direct sans if __name__ == "__main__" pour éviter les segfaults
main()

