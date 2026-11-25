# SkillMatch — Analyse intelligente des offres de stage et d'alternance

Application web locale qui rapproche un profil de compétences d'offres informatiques, explique les écarts et permet de suivre ses candidatures. Projet pédagogique de portfolio.

## Fonctionnalités

- Saisie des compétences et des domaines d'intérêt.
- Classement des offres avec un score explicable sur 100.
- Identification des compétences communes et manquantes.
- Filtres par ville et type de contrat.
- Suivi des candidatures enregistré dans SQLite.
- Interface web responsive, sans dépendance externe.

**Données :** les 12 offres et entreprises de démonstration sont entièrement fictives. L'application ne récupère pas d'offres réelles et n'envoie pas de candidatures.

## Lancer le projet

Prérequis : Python 3.10 ou supérieur. Aucune bibliothèque externe à installer.

```bash
python app.py
```

Ouvrir http://127.0.0.1:8000 dans le navigateur. Sous Windows, utiliser `py app.py` si la commande `python` n'est pas disponible. La base est créée automatiquement au premier démarrage. Arrêter le serveur avec Ctrl+C.

## Exemple d'utilisation

1. Saisir `Python, SQL, Git, Java, C++`.
2. Indiquer éventuellement `analyse de données, développement logiciel`.
3. Sélectionner Nantes et Alternance, puis cliquer sur **Analyser les offres**.
4. Consulter le classement, les compétences manquantes et mettre à jour le statut d'une candidature.

## Méthode de classement

Le score combine deux mesures :

- **Couverture des compétences (80 %)** : nombre de compétences requises déjà déclarées / nombre de compétences requises.
- **Similarité textuelle (20 %)** : similarité cosinus entre les vecteurs TF-IDF du profil et de chaque offre. La pondération TF-IDF utilise une fréquence logarithmique et un IDF lissé : `tf = 1 + ln(count)` et `idf = 1 + ln((N+1)/(df+1))`.

`score = round(100 × (0.8 × couverture + 0.2 × similarité))`

Les textes sont normalisés (casse et accents), et les termes comme C++ et TF-IDF sont conservés. La pondération est calculée sur l'ensemble des offres avant filtrage. Le score n'est ni une probabilité d'embauche ni une prédiction de recrutement : il s'agit d'un indicateur heuristique de proximité. TF-IDF est une méthode classique de NLP, sans entraînement de modèle supervisé ni IA générative.

## Architecture

```text
Navigateur (HTML/CSS)
       |
       v
app.py -- interface et routes HTTP
       |                     |
       v                     v
matching.py             database.py
TF-IDF + classement     SQLite + requêtes SQL
                             |
                             v
                     data/offers.json
                     (initialisation)
```

### Modèle relationnel

- `offers` : titre, entreprise, ville, contrat, description.
- `skills` : référentiel des compétences.
- `offer_skills` : relation plusieurs-à-plusieurs entre offres et compétences.
- `applications` : état de suivi d'une offre (clé étrangère vers `offers`).

Les requêtes utilisent des paramètres SQL et des jointures. Les statuts persistent après redémarrage. Le profil est transmis à l'interface via les paramètres de recherche, mais n'est pas enregistré dans SQLite.

## Structure du dépôt

```text
SkillMatch/
├── app.py
├── database.py
├── matching.py
├── data/
│   └── offers.json
├── static/
│   └── style.css
├── tests/
│   └── test_skillmatch.py
├── .gitignore
└── README.md
```

## Tests

Depuis le dossier du projet :

```bash
python -m unittest discover -s tests -v
```

Les tests couvrent l'initialisation idempotente de la base, les filtres, le classement, le profil vide, la normalisation, les scores sans correspondance et la persistance des statuts.

## Limites et évolutions possibles

- Jeu de données réduit et fictif, sans validation sur des offres réelles.
- Les compétences sont comparées à l'identique après normalisation ; des synonymes (par exemple POO/OOP) ne sont pas automatiquement reconnus.
- Pondération fixe choisie pour la démonstration ; elle pourrait être évaluée et ajustée sur des données annotées.
- Application locale mono-utilisateur ; pour une mise en ligne publique, prévoir un framework de production, authentification, protection CSRF et contrôle des accès.
- Pistes : import CSV, dictionnaire de synonymes et visualisation des compétences les plus demandées.
