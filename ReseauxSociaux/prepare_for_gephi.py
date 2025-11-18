"""
Prépare les données de passes NBA pour l'importation dans Gephi

Génère 2 fichiers CSV :
1. nodes.csv : Liste des joueurs (nœuds)
2. edges.csv : Liste des connexions de passes (arêtes)
"""

import pandas as pd
import os


def prepare_gephi_files(input_file, output_dir='gephi_data'):
    """
    Crée les fichiers nodes.csv et edges.csv pour Gephi
    
    Args:
        input_file (str): Chemin vers le fichier de données nettoyées
        output_dir (str): Dossier de sortie pour les fichiers Gephi
    """
    
    print("=" * 70)
    print("🎯 PRÉPARATION DES DONNÉES POUR GEPHI")
    print("=" * 70 + "\n")
    
    # Charger les données
    print(f"📂 Chargement : {input_file}")
    df = pd.read_csv(input_file)
    print(f"   {len(df)} connexions chargées\n")
    
    # ============================================================
    # 1. CRÉER LE FICHIER EDGES (ARÊTES)
    # ============================================================
    
    print("🔗 Création du fichier EDGES (arêtes)...")
    
    # Format Gephi pour les arêtes : Source, Target, Weight, Type
    edges = pd.DataFrame({
        'Source': df['PLAYER_ID'],                    # ID du passeur
        'Target': df['PASS_TEAMMATE_PLAYER_ID'],      # ID du receveur
        'Weight': df['AST'],                          # Poids = nombre d'assists
        'Passes': df['PASS'],                         # Info supplémentaire : total passes
        'Type': 'Directed'                            # Graphe orienté
    })
    
    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Sauvegarder les arêtes
    edges_file = os.path.join(output_dir, 'edges.csv')
    edges.to_csv(edges_file, index=False)
    print(f"   ✅ {len(edges)} arêtes sauvegardées : {edges_file}")
    print(f"   Colonnes : {list(edges.columns)}\n")
    
    # ============================================================
    # 2. CRÉER LE FICHIER NODES (NŒUDS)
    # ============================================================
    
    print("⚪ Création du fichier NODES (nœuds)...")
    
    # Extraire tous les joueurs uniques (passeurs + receveurs)
    passers = df[['PLAYER_ID', 'PLAYER_NAME_LAST_FIRST']].copy()
    passers.columns = ['Id', 'Label']
    
    receivers = df[['PASS_TEAMMATE_PLAYER_ID', 'PASS_TO']].copy()
    receivers.columns = ['Id', 'Label']
    
    # Combiner et supprimer les doublons
    nodes = pd.concat([passers, receivers]).drop_duplicates(subset='Id').reset_index(drop=True)
    
    # Calculer des métriques pour chaque joueur
    # Degré sortant (nombre d'assists donnés)
    out_degree = df.groupby('PLAYER_ID')['AST'].sum().reset_index()
    out_degree.columns = ['Id', 'Assists_Donnes']
    
    # Degré entrant (nombre d'assists reçus)
    in_degree = df.groupby('PASS_TEAMMATE_PLAYER_ID')['AST'].sum().reset_index()
    in_degree.columns = ['Id', 'Assists_Recus']
    
    # Fusionner avec les nœuds
    nodes = nodes.merge(out_degree, on='Id', how='left')
    nodes = nodes.merge(in_degree, on='Id', how='left')
    
    # Remplir les valeurs manquantes avec 0
    nodes['Assists_Donnes'] = nodes['Assists_Donnes'].fillna(0).astype(int)
    nodes['Assists_Recus'] = nodes['Assists_Recus'].fillna(0).astype(int)
    
    # Calculer le total d'assists (donnés + reçus)
    nodes['Total_Assists'] = nodes['Assists_Donnes'] + nodes['Assists_Recus']
    
    # Trier par impact total
    nodes = nodes.sort_values('Total_Assists', ascending=False).reset_index(drop=True)
    
    # Sauvegarder les nœuds
    nodes_file = os.path.join(output_dir, 'nodes.csv')
    nodes.to_csv(nodes_file, index=False)
    print(f"   ✅ {len(nodes)} nœuds sauvegardés : {nodes_file}")
    print(f"   Colonnes : {list(nodes.columns)}\n")
    
    # ============================================================
    # 3. AFFICHER LES STATISTIQUES
    # ============================================================
    
    print("=" * 70)
    print("📊 STATISTIQUES DU RÉSEAU")
    print("=" * 70)
    print(f"Nombre de joueurs (nœuds)      : {len(nodes)}")
    print(f"Nombre de connexions (arêtes)  : {len(edges)}")
    print(f"Total d'assists                : {edges['Weight'].sum()}")
    print(f"Total de passes                : {edges['Passes'].sum()}")
    print(f"Taux de réussite               : {(edges['Weight'].sum() / edges['Passes'].sum() * 100):.1f}%")
    print("=" * 70 + "\n")
    
    # Top 10 joueurs par impact
    print("🏆 TOP 10 JOUEURS (par total assists)")
    print("-" * 70)
    for idx, row in nodes.head(10).iterrows():
        print(f"   {row['Label']:30s} | Donnés: {row['Assists_Donnes']:4d} | Reçus: {row['Assists_Recus']:4d} | Total: {row['Total_Assists']:4d}")
    print("-" * 70 + "\n")
    
    # ============================================================
    # 4. INSTRUCTIONS POUR GEPHI
    # ============================================================
    
    print("=" * 70)
    print("📖 INSTRUCTIONS POUR GEPHI")
    print("=" * 70)
    print("\n1️⃣  Importer les NŒUDS :")
    print(f"    - Fichier : {nodes_file}")
    print("    - Data Laboratory > Import Spreadsheet")
    print("    - Sélectionner : 'Nodes table'")
    print("    - Colonne 'Id' comme identifiant unique")
    
    print("\n2️⃣  Importer les ARÊTES :")
    print(f"    - Fichier : {edges_file}")
    print("    - Data Laboratory > Import Spreadsheet")
    print("    - Sélectionner : 'Edges table'")
    print("    - Graph Type : 'Directed' (orienté)")
    
    print("\n3️⃣  Visualisation suggérée :")
    print("    - Layout : ForceAtlas 2 ou Yifan Hu")
    print("    - Taille des nœuds : 'Total_Assists' ou 'Assists_Donnes'")
    print("    - Épaisseur des arêtes : 'Weight' (assists)")
    print("    - Couleur des nœuds : Modularity (détection de communautés)")
    
    print("\n4️⃣  Métriques ARS à calculer dans Gephi :")
    print("    - Statistics > Average Degree")
    print("    - Statistics > Network Diameter")
    print("    - Statistics > Modularity (communautés)")
    print("    - Statistics > PageRank")
    print("    - Statistics > Betweenness Centrality")
    
    print("\n" + "=" * 70 + "\n")
    
    return nodes, edges


def main():
    """Fonction principale"""
    
    # Fichier d'entrée (données nettoyées)
    input_file = "data/GSW_2018-19_passes_clean.csv"
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_file):
        print(f"❌ Erreur : Fichier introuvable : {input_file}")
        print("   Exécutez d'abord : python clean_pass_data.py")
        return
    
    # Préparer les fichiers pour Gephi
    nodes, edges = prepare_gephi_files(input_file, output_dir='gephi_data')
    
    print("✅ Fichiers prêts pour l'importation dans Gephi !")
    print(f"📁 Dossier : gephi_data/")
    print(f"   - nodes.csv ({len(nodes)} joueurs)")
    print(f"   - edges.csv ({len(edges)} connexions)\n")


if __name__ == "__main__":
    main()
