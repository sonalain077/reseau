# 🏀 PROJET D'ANALYSE DES RÉSEAUX SOCIAUX (ARS) DANS LA NBA

## 1. Sujet du Projet
**Titre :** Analyse des Réseaux de Passes Offensives : Étude Comparative des Topologies Réseautiques et de l'Efficacité en NBA.

**Objectif Principal :** Utiliser l'Analyse des Réseaux Sociaux (ARS) pour quantifier et comparer les différences de structure de collaboration (réseau de passes) entre une équipe de haut de classement et une équipe de bas de classement, et déterminer l'impact de ces topologies sur la performance offensive.

---

## 2. Période et Équipes Cibles (Contraste Structurel)

Afin de maximiser le contraste des philosophies de jeu et la pertinence de l'analyse ARS, le projet se concentrera sur la saison et les équipes suivantes :

| Élément | Choix / Justification |
| :--- | :--- |
| **Saison de Couverture** | **Saison NBA 2018-2019.** (Période récente idéale pour les données de *tracking* et un contraste tactique net). |
| **Équipe 1 (Haut de Classement / Distribuée)** | **Golden State Warriors (GSW) 2018-2019.** (Archétype du mouvement de balle, haute collaboration). **Attendu :** Réseau à **haute densité** et **faible centralisation**. |
| **Équipe 2 (Bas de Classement / Centralisée)** | **Houston Rockets (HOU) 2018-2019.** (Archétype de l'isolation autour de James Harden). **Attendu :** Réseau à **faible densité** et **très forte centralisation**. |

---

## 3. Modélisation et Métriques ARS

Le réseau sera construit à partir des données de passes réussies (*Play-by-Play* et *Tracking Data*).

| Composante ARS | Définition dans le Contexte NBA | Métriques Clés |
| :--- | :--- | :--- |
| **Nœuds** | Les joueurs présents sur le terrain (5 par possession). | *Aucune* |
| **Arêtes** | Les passes réussies entre les joueurs (réseau **dirigé** et **pondéré**). | *Aucune* |
| **Structure Globale** | Mesure de la cohésion et de la distribution du ballon de l'équipe. | **Densité** (proportion de liens existants) ; **Centralisation** (concentration des passes). |
| **Rôles Individuels** | Mesure de l'importance et de la fonction de chaque joueur dans le flux. | **Centralité de Degré** (Passeurs/Receveurs actifs) ; **Centralité d'Intermédiarité** (Joueurs-Pivots/Relais) ; **Centralité de PageRank** (Influence). |

---

## 4. Questions de Recherche Clés

1.  **Corrélation Performance/Densité :** Comment la densité du réseau de passes et le niveau de centralisation sont-ils corrélés avec l'efficacité offensive (*Net Rating Offensif*) des deux équipes ?
2.  **Rôles Contrastés :** Quelles sont les différences dans la distribution des rôles mesurées par les métriques de Centralité entre l'équipe de haut de classement (GSW) et celle de bas de classement (HOU) ?

---

## 5. Objectif de l'Analyse

Démontrer que les différences dans la structure de collaboration mesurées par l'ARS (un réseau plus robuste et distribué vs. un réseau dépendant et fragile) constituent un **facteur explicatif** de la disparité de performance entre les deux équipes sélectionnées.