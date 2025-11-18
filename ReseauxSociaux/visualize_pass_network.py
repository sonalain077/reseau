"""
Visualisation du réseau de passes NBA avec filtrage des relations importantes

Objectif : Créer des graphes lisibles en filtrant les connexions les plus significatives
pour l'analyse ARS (densité, centralisation, centralité)
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os


def load_pass_data(file_path):
    """Charge les données de passes"""
    print(f"📂 Chargement des données : {file_path}")
    df = pd.read_csv(file_path)
    print(f"   {len(df)} connexions chargées\n")
    return df


def build_network(df, weight_column='AST', min_weight=0):
    """
    Construit un graphe NetworkX à partir des données de passes
    
    Args:
        df: DataFrame avec les passes
        weight_column: Colonne à utiliser comme poids ('AST' ou 'PASS')
        min_weight: Seuil minimum pour inclure une connexion
    
    Returns:
        nx.DiGraph: Graphe orienté
    """
    G = nx.DiGraph()
    
    # Filtrer par poids minimum
    df_filtered = df[df[weight_column] >= min_weight].copy()
    
    print(f"🔨 Construction du réseau (seuil min: {min_weight} {weight_column})")
    print(f"   Connexions conservées : {len(df_filtered)} / {len(df)}")
    
    # Ajouter les arêtes avec poids
    for _, row in df_filtered.iterrows():
        passer = row['PLAYER_NAME']
        receiver = row['PASS_TO']
        weight = row[weight_column]
        
        G.add_edge(passer, receiver, weight=weight)
    
    print(f"   Nœuds (joueurs) : {G.number_of_nodes()}")
    print(f"   Arêtes (connexions) : {G.number_of_edges()}")
    print(f"   Densité : {nx.density(G):.3f}\n")
    
    return G


def calculate_centralities(G):
    """Calcule les métriques de centralité pour tous les nœuds"""
    print("📊 Calcul des centralités...")
    
    centralities = {
        'degree_in': dict(G.in_degree(weight='weight')),
        'degree_out': dict(G.out_degree(weight='weight')),
        'betweenness': nx.betweenness_centrality(G, weight='weight'),
        'pagerank': nx.pagerank(G, weight='weight'),
    }
    
    # Créer un DataFrame pour faciliter l'analyse
    df_centrality = pd.DataFrame({
        'Joueur': list(G.nodes()),
        'Degré_Entrant': [centralities['degree_in'][n] for n in G.nodes()],
        'Degré_Sortant': [centralities['degree_out'][n] for n in G.nodes()],
        'Intermédiarité': [centralities['betweenness'][n] for n in G.nodes()],
        'PageRank': [centralities['pagerank'][n] for n in G.nodes()],
    })
    
    print("✅ Centralités calculées\n")
    return centralities, df_centrality


def print_top_players(df_centrality, top_n=10):
    """Affiche les joueurs les plus importants selon différentes métriques"""
    
    print("=" * 70)
    print("🏆 TOP JOUEURS PAR CENTRALITÉ")
    print("=" * 70)
    
    metrics = {
        'Degré_Sortant': '🎯 Meilleurs PASSEURS (Degré Sortant)',
        'Degré_Entrant': '🎯 Meilleurs RECEVEURS (Degré Entrant)',
        'Intermédiarité': '🔗 Meilleurs RELAIS (Intermédiarité)',
        'PageRank': '⭐ Plus INFLUENTS (PageRank)',
    }
    
    for metric, title in metrics.items():
        print(f"\n{title}")
        print("-" * 70)
        top = df_centrality.nlargest(top_n, metric)
        for idx, row in top.iterrows():
            print(f"   {row['Joueur']:30s} : {row[metric]:.2f}")
    
    print("=" * 70 + "\n")


def visualize_network(G, df_centrality, title="Réseau de Passes NBA", 
                     node_size_metric='PageRank', edge_width_scale=0.05,
                     layout='spring', figsize=(18, 14)):
    """
    Visualise le réseau avec des paramètres personnalisables
    
    Args:
        G: Graphe NetworkX
        df_centrality: DataFrame avec les centralités
        title: Titre du graphe
        node_size_metric: Métrique pour la taille des nœuds
        edge_width_scale: Échelle pour l'épaisseur des arêtes
        layout: Type de layout ('spring', 'circular', 'kamada_kawai')
    """
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Choisir le layout
    print(f"🎨 Génération de la visualisation (layout: {layout})...")
    if layout == 'spring':
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42)
    
    # Tailles des nœuds basées sur la métrique choisie
    node_sizes = []
    for node in G.nodes():
        metric_value = df_centrality[df_centrality['Joueur'] == node][node_size_metric].values[0]
        node_sizes.append(300 + metric_value * 5000)  # Scale pour visualisation
    
    # Couleurs des nœuds basées sur PageRank
    node_colors = [df_centrality[df_centrality['Joueur'] == n]['PageRank'].values[0] 
                   for n in G.nodes()]
    
    # Épaisseur des arêtes basée sur le poids
    edge_widths = [G[u][v]['weight'] * edge_width_scale for u, v in G.edges()]
    
    # Dessiner les arêtes
    nx.draw_networkx_edges(
        G, pos,
        width=edge_widths,
        alpha=0.3,
        edge_color='gray',
        arrowsize=20,
        arrowstyle='->',
        connectionstyle='arc3,rad=0.1',
        ax=ax
    )
    
    # Dessiner les nœuds
    nodes = nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.YlOrRd,
        alpha=0.9,
        ax=ax
    )
    
    # Dessiner les labels
    nx.draw_networkx_labels(
        G, pos,
        font_size=9,
        font_weight='bold',
        font_color='black',
        ax=ax
    )
    
    # Colorbar pour PageRank
    plt.colorbar(nodes, ax=ax, label='PageRank (Influence)')
    
    # Titre et style
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.axis('off')
    
    plt.tight_layout()
    print("✅ Visualisation générée\n")
    
    return fig


def save_network_data(G, df_centrality, output_dir='output'):
    """Sauvegarde les données du réseau et les métriques"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Sauvegarder les centralités
    centrality_file = os.path.join(output_dir, 'player_centralities.csv')
    df_centrality.to_csv(centrality_file, index=False)
    print(f"💾 Centralités sauvegardées : {centrality_file}")
    
    # Sauvegarder la liste des arêtes
    edges_file = os.path.join(output_dir, 'network_edges.csv')
    edges_data = []
    for u, v, data in G.edges(data=True):
        edges_data.append({
            'Source': u,
            'Target': v,
            'Weight': data['weight']
        })
    pd.DataFrame(edges_data).to_csv(edges_file, index=False)
    print(f"💾 Arêtes sauvegardées : {edges_file}")
    
    # Métriques globales du réseau
    metrics = {
        'Nombre de joueurs': G.number_of_nodes(),
        'Nombre de connexions': G.number_of_edges(),
        'Densité': nx.density(G),
        'Diamètre': nx.diameter(G.to_undirected()) if nx.is_connected(G.to_undirected()) else 'N/A',
    }
    
    metrics_file = os.path.join(output_dir, 'network_metrics.txt')
    with open(metrics_file, 'w') as f:
        f.write("MÉTRIQUES DU RÉSEAU\n")
        f.write("=" * 50 + "\n")
        for key, value in metrics.items():
            f.write(f"{key}: {value}\n")
    print(f"💾 Métriques globales sauvegardées : {metrics_file}\n")


def main():
    """Fonction principale"""
    
    print("=" * 70)
    print("🏀 ANALYSE DU RÉSEAU DE PASSES NBA")
    print("=" * 70 + "\n")
    
    # 1. Charger les données
    data_file = "GSW_2018-19_passes_clean.csv"
    if not os.path.exists(data_file):
        data_file = "data/GSW_2018-19_passes_clean.csv"
        if not os.path.exists(data_file):
            print("❌ Fichier de données introuvable!")
            return
    
    df = load_pass_data(data_file)
    
    # 2. Créer plusieurs visualisations avec différents seuils
    thresholds = [
        (0, "Tous les assists", 0.02),      # Toutes les connexions
        (5, "Assists >= 5", 0.05),           # Connexions moyennes
        (10, "Assists >= 10", 0.08),         # Connexions fortes
        (20, "Assists >= 20", 0.1),          # Connexions très fortes
    ]
    
    for min_assists, label, edge_scale in thresholds:
        print(f"\n{'='*70}")
        print(f"📊 ANALYSE : {label}")
        print(f"{'='*70}\n")
        
        # Construire le réseau
        G = build_network(df, weight_column='AST', min_weight=min_assists)
        
        if G.number_of_nodes() == 0:
            print(f"⚠️  Aucun nœud avec ce seuil, passage au suivant...\n")
            continue
        
        # Calculer les centralités
        centralities, df_centrality = calculate_centralities(G)
        
        # Afficher le top des joueurs
        print_top_players(df_centrality, top_n=10)
        
        # Visualiser
        title = f"GSW 2018-19 - Réseau de Passes ({label})"
        fig = visualize_network(
            G, df_centrality, 
            title=title,
            node_size_metric='PageRank',
            edge_width_scale=edge_scale,
            layout='spring'
        )
        
        # Sauvegarder
        os.makedirs('output', exist_ok=True)
        filename = f"output/GSW_network_ast{min_assists}.png"
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"💾 Graphe sauvegardé : {filename}\n")
        
        # Sauvegarder les données uniquement pour le réseau complet
        if min_assists == 0:
            save_network_data(G, df_centrality)
    
    # Afficher tous les graphes
    plt.show()
    
    print("=" * 70)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 70)


if __name__ == "__main__":
    main()
