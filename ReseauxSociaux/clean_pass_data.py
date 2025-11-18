"""
Script de nettoyage et préparation des données de passes NBA
pour l'Analyse des Réseaux Sociaux (ARS)

Objectif : Conserver uniquement les features essentielles pour l'analyse
des topologies réseautiques et la construction du graphe de passes.
"""

import pandas as pd
import os


def clean_pass_data(input_file, output_file=None):
    """
    Nettoie les données de passes en gardant uniquement les colonnes essentielles
    pour l'analyse ARS.
    
    Args:
        input_file (str): Chemin vers le fichier CSV brut
        output_file (str): Chemin vers le fichier nettoyé (optionnel)
    
    Returns:
        pd.DataFrame: DataFrame nettoyé
    """
    
    print(f"📂 Lecture du fichier : {input_file}")
    df = pd.read_csv(input_file)
    print(f"   Dimensions initiales : {df.shape}")
    print(f"   Colonnes disponibles : {list(df.columns)}\n")
    
    # ============================================================
    # SUPPRESSION DES COLONNES NON ESSENTIELLES
    # ============================================================
    
    columns_to_drop = [
        'TEAM_NAME',
        'TEAM_ID', 
        'TEAM_ABBREVIATION',
        'PASS_TYPE',
        'G',
        'FREQUENCY',
        'FGM',
        'FGA',
        'FG_PCT',
        'FG2M',
        'FG2A',
        'FG2_PCT',
        'FG3M',
        'FG3A',
        'FG3_PCT',
        'PLAYER_NAME'
    ]
    
    # Supprimer les colonnes non essentielles
    df_clean = df.drop(columns=columns_to_drop, errors='ignore')
    
    print(f"❌ Colonnes supprimées : {[col for col in columns_to_drop if col in df.columns]}")
    print(f"✅ Colonnes conservées : {list(df_clean.columns)}\n")
    
    # ============================================================
    # FEATURES ESSENTIELLES POUR L'ARS (conservées)
    # ============================================================
    # PLAYER_ID                   - ID du passeur (nœud source)
    # PASS_TEAMMATE_PLAYER_ID     - ID du receveur (nœud cible)
    # PLAYER_NAME_LAST_FIRST      - Nom du passeur (pour visualisation)
    # PASS_TO                     - Nom du receveur (pour visualisation)
    # PASS                        - Nombre total de passes
    # AST                         - Assists (passes → panier) - POIDS PRINCIPAL
    # ============================================================
    
    # ============================================================
    # NETTOYAGE DES DONNÉES
    # ============================================================
    
    print("🧹 Nettoyage en cours...")
    
    initial_rows = len(df_clean)
    
    # 1. Supprimer les valeurs manquantes critiques
    df_clean = df_clean.dropna(subset=['PLAYER_ID', 'PASS_TEAMMATE_PLAYER_ID', 'PASS', 'AST'])
    removed_na = initial_rows - len(df_clean)
    if removed_na > 0:
        print(f"   - {removed_na} lignes avec valeurs manquantes supprimées")
    
    # 2. Supprimer les auto-passes (joueur se passe à lui-même)
    initial_after_na = len(df_clean)
    self_passes = df_clean[df_clean['PLAYER_ID'] == df_clean['PASS_TEAMMATE_PLAYER_ID']]
    if len(self_passes) > 0:
        df_clean = df_clean[df_clean['PLAYER_ID'] != df_clean['PASS_TEAMMATE_PLAYER_ID']]
        print(f"   - {len(self_passes)} auto-passes supprimées")
    
    # NOTE : On garde TOUTES les lignes, même avec AST=0
    # Cela permet d'analyser TOUTES les tentatives de passes, pas seulement les assists réussis
    
    # 4. Nettoyer les noms (trim whitespace)
    if 'PLAYER_NAME_LAST_FIRST' in df_clean.columns:
        df_clean['PLAYER_NAME_LAST_FIRST'] = df_clean['PLAYER_NAME_LAST_FIRST'].str.strip()
    df_clean['PASS_TO'] = df_clean['PASS_TO'].str.strip()
    
    # 5. Trier par nombre d'assists (décroissant) - métrique la plus pertinente
    df_clean = df_clean.sort_values('AST', ascending=False).reset_index(drop=True)
    
    print(f"   ✅ Nettoyage terminé\n")
    
    # ============================================================
    # STATISTIQUES DESCRIPTIVES
    # ============================================================
    
    print("📊 STATISTIQUES DESCRIPTIVES")
    print("=" * 60)
    print(f"Nombre total de connexions (arêtes) : {len(df_clean)}")
    print(f"Nombre de joueurs uniques (passeurs) : {df_clean['PLAYER_ID'].nunique()}")
    print(f"Nombre de joueurs uniques (receveurs) : {df_clean['PASS_TEAMMATE_PLAYER_ID'].nunique()}")
    print(f"Nombre total d'assists : {df_clean['AST'].sum()}")
    print(f"Nombre total de passes : {df_clean['PASS'].sum()}")
    print(f"Taux assists/passes : {(df_clean['AST'].sum() / df_clean['PASS'].sum() * 100):.1f}%")
    print(f"Moyenne d'assists par connexion : {df_clean['AST'].mean():.2f}")
    print(f"Médiane d'assists par connexion : {df_clean['AST'].median():.2f}")
    print(f"Max assists sur une connexion : {df_clean['AST'].max()}")
    print("=" * 60)
    
    # Top 10 connexions les plus fortes (par assists)
    print("\n🔝 TOP 10 CONNEXIONS LES PLUS FORTES (par assists)")
    print("-" * 70)
    display_cols = ['PASS_TO', 'AST', 'PASS']
    if 'PLAYER_NAME_LAST_FIRST' in df_clean.columns:
        display_cols.insert(0, 'PLAYER_NAME_LAST_FIRST')
    top_connections = df_clean.head(10)[display_cols]
    for idx, row in top_connections.iterrows():
        passer = row.get('PLAYER_NAME_LAST_FIRST', str(row.get('PLAYER_ID', 'N/A')))
        print(f"   {passer:30s} → {row['PASS_TO']:20s} : {int(row['AST']):3d} AST / {int(row['PASS']):3d} passes")
    print("-" * 70)
    
    # Top 10 passeurs
    print("\n🎯 TOP 10 PASSEURS (Centralité de Degré Sortant)")
    print("-" * 60)
    group_col = 'PLAYER_NAME_LAST_FIRST' if 'PLAYER_NAME_LAST_FIRST' in df_clean.columns else 'PLAYER_ID'
    top_passers = df_clean.groupby(group_col)['AST'].sum().sort_values(ascending=False).head(10)
    for player, assists in top_passers.items():
        print(f"   {str(player):30s} : {int(assists):4d} assists")
    print("-" * 60)
    
    # Top 10 receveurs
    print("\n🎯 TOP 10 RECEVEURS (Centralité de Degré Entrant)")
    print("-" * 60)
    top_receivers = df_clean.groupby('PASS_TO')['AST'].sum().sort_values(ascending=False).head(10)
    for player, assists in top_receivers.items():
        print(f"   {player:30s} : {int(assists):4d} assists reçus")
    print("-" * 60)
    
    # ============================================================
    # SAUVEGARDE
    # ============================================================
    
    if output_file is None:
        # Créer un nom de fichier automatique
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_clean.csv"
    
    # Créer le dossier si nécessaire
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    df_clean.to_csv(output_file, index=False)
    print(f"\n💾 Données nettoyées sauvegardées : {output_file}")
    print(f"   Dimensions finales : {df_clean.shape}\n")
    
    return df_clean


def main():
    """Fonction principale"""
    
    # Fichier d'entrée (données brutes)
    input_file = "GSW_2018-19_passes.csv"
    
    # Vérifier si le fichier existe
    if not os.path.exists(input_file):
        # Essayer dans le dossier data/
        input_file = "data/GSW_2018-19_passes.csv"
        if not os.path.exists(input_file):
            print(f"❌ Erreur : Fichier introuvable")
            print(f"   Cherché dans : GSW_2018-19_passes.csv et data/GSW_2018-19_passes.csv")
            return
    
    # Fichier de sortie (données nettoyées)
    output_file = "data/GSW_2018-19_passes_clean.csv"
    
    # Nettoyer les données
    df_clean = clean_pass_data(input_file, output_file)
    
    print("✅ Traitement terminé avec succès!")
    print("\n💡 Prochaines étapes :")
    print("   1. Construire le graphe NetworkX avec les données nettoyées")
    print("   2. Calculer les métriques ARS (densité, centralisation)")
    print("   3. Calculer les centralités individuelles (degré, intermédiarité, PageRank)")
    print("   4. Répéter pour HOU 2018-19 et comparer les structures")


if __name__ == "__main__":
    main()
