from playwright.sync_api import sync_playwright
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
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


def pass_web(team, ssn, web):
    """Scrape NBA passes et affiche le graphe réseau."""
    print(f"Scraping {team} ({ssn}) - {web}")

    with sync_playwright() as p:
        # --- Étape 1 : récupérer la liste des joueurs ---
        team_id = 1610612744  # GSW par défaut
        url_players = (
            f"https://stats.nba.com/stats/commonteamroster?TeamID={team_id}&Season={ssn}"
        )

        players_data = fetch_nba_json(p, url_players)
        rows = players_data["resultSets"][0]["rowSet"]
        headers = players_data["resultSets"][0]["headers"]
        df_roster = pd.DataFrame(rows, columns=headers)
        player_ids = df_roster["PLAYER_ID"].tolist()
        player_names = df_roster["PLAYER"].tolist()

        print(f"{len(player_ids)} joueurs trouvés.")

        df_list = []

        # --- Étape 2 : récupérer les passes pour chaque joueur ---
        for pid, name in zip(player_ids, player_names):
            url_pass = (
                "https://stats.nba.com/stats/playerdashptpass?"
                f"DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&"
                f"Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&"
                f"PerMode=Totals&Period=0&PlayerID={pid}&Season={ssn}&"
                "SeasonSegment=&SeasonType=Regular+Season&TeamID=0&"
                "VsConference=&VsDivision="
            )

            try:
                data = fetch_nba_json(p, url_pass)
                if not data["resultSets"]:
                    continue
                passes = data["resultSets"][0]
                df = pd.DataFrame(passes["rowSet"], columns=passes["headers"])
                df["PLAYER_NAME"] = name
                df_list.append(df)
                print(f"✓ {name} : {len(df)} passes récupérées")
            except Exception as e:
                print(f"⚠️ Erreur {name} : {e}")
                continue

        if not df_list:
            print("Aucune donnée trouvée.")
            return

        df_all = pd.concat(df_list, ignore_index=True)
        print(f"Total passes récupérées : {len(df_all)}")

        # --- Étape 3 : création du graphe ---
        G = nx.DiGraph()
        for _, row in df_all.iterrows():
            passer = row["PLAYER_NAME"]
            receiver = row["PASS_TO"]
            weight = row["PASS"]
            G.add_edge(passer, receiver, weight=weight)

        # --- Étape 3 bis : enregistrement des données ---
        os.makedirs("data", exist_ok=True)
        csv_path = f"data/{team}_{ssn}_passes.csv"
        df_all.to_csv(csv_path, index=False)
        print(f"✅ Données sauvegardées dans {csv_path}")

        # --- Étape 4 : affichage du graphe ---
        plt.figure(figsize=(16, 12))

        # Disposition plus lisible
        pos = nx.spring_layout(G, k=2, iterations=200, seed=42)

        # Taille des nœuds selon leur degré
        node_sizes = [300 + 15 * G.degree(n) for n in G.nodes()]

        nx.draw_networkx_edges(
            G, pos,
            arrowstyle="->", arrowsize=15,
            edge_color="lightblue",
            width=[d["weight"] / 5 for _, _, d in G.edges(data=True)]
        )
        nx.draw_networkx_nodes(G, pos, node_color="skyblue", node_size=node_sizes)
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

        plt.title(f"NBA Pass Network – {team} ({ssn})", fontsize=16)
        plt.axis("off")
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    pass_web("GSW", "2018-19", "AST")
