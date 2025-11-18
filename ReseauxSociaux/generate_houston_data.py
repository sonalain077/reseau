"""
Script pour générer les données NBA pour Houston Rockets 2018-19
et préparer automatiquement pour Gephi
"""

from playwright.sync_api import sync_playwright
import pandas as pd
import os


def fetch_nba_json(playwright, url):
    """Effectue une requête NBA via Playwright (bypass CORS & Cloudflare)."""
    browser = playwright.chromium.launch(headless=True)
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    context = browser.new_context(user_agent=user_agent)
    page = context.new_page()

    # Aller une fois sur le site pour initier les cookies
    page.goto("https://stats.nba.com", timeout=60000)

    headers = {
        "Host": "stats.nba.com",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "Referer": "https://stats.nba.com/",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = context.request.get(url, headers=headers, timeout=60000)
        if response.status != 200:
            raise RuntimeError(f"Erreur HTTP {response.status}")
        data = response.json()
    except Exception as e:
        browser.close()
        raise RuntimeError(f"Erreur lors de la requête Playwright : {e}")
    browser.close()
    return data


def scrape_team_passes(team_abbr, team_id, season):
    """
    Scrape les données de passes d'une équipe NBA
    
    Args:
        team_abbr (str): Abréviation de l'équipe (ex: 'HOU', 'GSW')
        team_id (int): ID NBA de l'équipe
        season (str): Saison (ex: '2018-19')
    """
    
    print("=" * 70)
    print(f"🏀 SCRAPING NBA - {team_abbr} {season}")
    print("=" * 70 + "\n")
    
    with sync_playwright() as p:
        # --- Étape 1 : récupérer la liste des joueurs ---
        print(f"📋 Récupération de la liste des joueurs {team_abbr}...")
        url_players = (
            f"https://stats.nba.com/stats/commonteamroster?TeamID={team_id}&Season={season}"
        )

        players_data = fetch_nba_json(p, url_players)
        rows = players_data["resultSets"][0]["rowSet"]
        headers = players_data["resultSets"][0]["headers"]
        df_roster = pd.DataFrame(rows, columns=headers)
        player_ids = df_roster["PLAYER_ID"].tolist()
        player_names = df_roster["PLAYER"].tolist()

        print(f"   ✅ {len(player_ids)} joueurs trouvés\n")

        df_list = []

        # --- Étape 2 : récupérer les passes pour chaque joueur ---
        print(f"🔄 Scraping des statistiques de passes...")
        for i, (pid, name) in enumerate(zip(player_ids, player_names), 1):
            url_pass = (
                "https://stats.nba.com/stats/playerdashptpass?"
                f"DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&"
                f"Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&"
                f"PerMode=Totals&Period=0&PlayerID={pid}&Season={season}&"
                "SeasonSegment=&SeasonType=Regular+Season&TeamID=0&"
                "VsConference=&VsDivision="
            )

            try:
                data = fetch_nba_json(p, url_pass)
                if not data["resultSets"]:
                    print(f"   [{i}/{len(player_ids)}] ⚠️ {name} : Aucune donnée")
                    continue
                passes = data["resultSets"][0]
                df = pd.DataFrame(passes["rowSet"], columns=passes["headers"])
                df["PLAYER_NAME"] = name
                df_list.append(df)
                print(f"   [{i}/{len(player_ids)}] ✓ {name} : {len(df)} connexions")
            except Exception as e:
                print(f"   [{i}/{len(player_ids)}] ⚠️ {name} : Erreur - {e}")
                continue

        if not df_list:
            print("\n❌ Aucune donnée trouvée.")
            return None

        df_all = pd.concat(df_list, ignore_index=True)
        print(f"\n✅ Total : {len(df_all)} connexions récupérées\n")

        # --- Étape 3 : enregistrement des données brutes ---
        os.makedirs("data", exist_ok=True)
        raw_csv_path = f"{team_abbr}_{season}_passes.csv"
        df_all.to_csv(raw_csv_path, index=False)
        print(f"💾 Données brutes sauvegardées : {raw_csv_path}\n")
        
        return raw_csv_path


def clean_and_prepare_gephi(raw_file, team_abbr, season):
    """
    Nettoie les données et prépare les fichiers pour Gephi
    """
    
    print("=" * 70)
    print(f"🧹 NETTOYAGE ET PRÉPARATION GEPHI - {team_abbr} {season}")
    print("=" * 70 + "\n")
    
    # Charger les données
    df = pd.read_csv(raw_file)
    print(f"📂 Données chargées : {len(df)} lignes\n")
    
    # Colonnes à supprimer
    columns_to_drop = [
        'TEAM_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION', 'PASS_TYPE', 'G', 'FREQUENCY',
        'FGM', 'FGA', 'FG_PCT', 'FG2M', 'FG2A', 'FG2_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
        'PLAYER_NAME'
    ]
    
    df_clean = df.drop(columns=columns_to_drop, errors='ignore')
    
    # Supprimer les auto-passes
    initial = len(df_clean)
    df_clean = df_clean[df_clean['PLAYER_ID'] != df_clean['PASS_TEAMMATE_PLAYER_ID']]
    print(f"🧹 {initial - len(df_clean)} auto-passes supprimées")
    
    # Sauvegarder les données nettoyées
    clean_file = f"data/{team_abbr}_{season}_passes_clean.csv"
    df_clean.to_csv(clean_file, index=False)
    print(f"💾 Données nettoyées : {clean_file}\n")
    
    # ============================================================
    # CRÉER LES FICHIERS GEPHI
    # ============================================================
    
    print("🎯 Création des fichiers Gephi...\n")
    
    # 1. EDGES (arêtes)
    edges = pd.DataFrame({
        'Source': df_clean['PLAYER_ID'],
        'Target': df_clean['PASS_TEAMMATE_PLAYER_ID'],
        'Weight': df_clean['AST'],
        'Passes': df_clean['PASS'],
        'Type': 'Directed'
    })
    
    # 2. NODES (nœuds)
    passers = df_clean[['PLAYER_ID', 'PLAYER_NAME_LAST_FIRST']].copy()
    passers.columns = ['Id', 'Label']
    
    receivers = df_clean[['PASS_TEAMMATE_PLAYER_ID', 'PASS_TO']].copy()
    receivers.columns = ['Id', 'Label']
    
    nodes = pd.concat([passers, receivers]).drop_duplicates(subset='Id').reset_index(drop=True)
    
    # Métriques
    out_degree = df_clean.groupby('PLAYER_ID')['AST'].sum().reset_index()
    out_degree.columns = ['Id', 'Assists_Donnes']
    
    in_degree = df_clean.groupby('PASS_TEAMMATE_PLAYER_ID')['AST'].sum().reset_index()
    in_degree.columns = ['Id', 'Assists_Recus']
    
    nodes = nodes.merge(out_degree, on='Id', how='left')
    nodes = nodes.merge(in_degree, on='Id', how='left')
    nodes['Assists_Donnes'] = nodes['Assists_Donnes'].fillna(0).astype(int)
    nodes['Assists_Recus'] = nodes['Assists_Recus'].fillna(0).astype(int)
    nodes['Total_Assists'] = nodes['Assists_Donnes'] + nodes['Assists_Recus']
    nodes = nodes.sort_values('Total_Assists', ascending=False).reset_index(drop=True)
    
    # Sauvegarder
    gephi_dir = f"gephi_data_{team_abbr}"
    os.makedirs(gephi_dir, exist_ok=True)
    
    edges_file = os.path.join(gephi_dir, 'edges.csv')
    nodes_file = os.path.join(gephi_dir, 'nodes.csv')
    
    edges.to_csv(edges_file, index=False)
    nodes.to_csv(nodes_file, index=False)
    
    print(f"✅ Fichiers Gephi créés dans : {gephi_dir}/")
    print(f"   - nodes.csv : {len(nodes)} joueurs")
    print(f"   - edges.csv : {len(edges)} connexions\n")
    
    # Statistiques
    print("=" * 70)
    print("📊 STATISTIQUES")
    print("=" * 70)
    print(f"Joueurs             : {len(nodes)}")
    print(f"Connexions          : {len(edges)}")
    print(f"Total assists       : {edges['Weight'].sum()}")
    print(f"Total passes        : {edges['Passes'].sum()}")
    print(f"Taux de réussite    : {(edges['Weight'].sum() / edges['Passes'].sum() * 100):.1f}%")
    print("=" * 70 + "\n")
    
    print("🏆 TOP 10 JOUEURS")
    print("-" * 70)
    for _, row in nodes.head(10).iterrows():
        print(f"   {row['Label']:30s} | D:{row['Assists_Donnes']:4d} R:{row['Assists_Recus']:4d} T:{row['Total_Assists']:4d}")
    print("-" * 70 + "\n")


def main():
    """Fonction principale"""
    
    # Configuration des équipes
    teams = [
        {"abbr": "HOU", "id": 1610612745, "name": "Houston Rockets"},
        # {"abbr": "GSW", "id": 1610612744, "name": "Golden State Warriors"},  # Déjà fait
    ]
    
    season = "2018-19"
    
    for team in teams:
        print("\n" + "🔥" * 35)
        print(f"   {team['name']} ({team['abbr']}) - Saison {season}")
        print("🔥" * 35 + "\n")
        
        # 1. Scraper les données
        raw_file = scrape_team_passes(team['abbr'], team['id'], season)
        
        if raw_file:
            # 2. Nettoyer et préparer pour Gephi
            clean_and_prepare_gephi(raw_file, team['abbr'], season)
    
    print("\n" + "=" * 70)
    print("✅ TRAITEMENT TERMINÉ POUR TOUTES LES ÉQUIPES")
    print("=" * 70)


if __name__ == "__main__":
    main()
