# Gestionnaire de Bibliothèque XML

Ce projet fournit un petit programme en Python permettant de gérer une bibliothèque stockée dans un fichier XML. Il permet d'ajouter des ouvrages et des utilisateurs, ainsi que de suivre les emprunts.

## Prérequis
- Python 3.8 ou version supérieure

## Installation
Aucune installation spécifique n'est nécessaire. Clonez simplement le dépôt et exécutez le fichier `main.py`.

```bash
python main.py --help
```

## Commandes principales
- `add-book <titre> <auteur> <genre> <annee>` : ajoute un livre
- `list-books` : liste tous les livres
- `search-books [--author AUTEUR] [--genre GENRE] [--year ANNEE]` : recherche dans la bibliothèque
- `add-user <nom>` : ajoute un utilisateur
- `loan-book <id_livre> <id_utilisateur> [date_sortie] [date_retour_prevue]` : enregistre un emprunt
- `return-book <id_livre> [date_retour]` : marque un livre comme rendu
- `list-loans` : affiche les emprunts

## Exemple d'utilisation
```bash
python main.py add-book "Le Mandat" "Ousmane Sembène" Roman 1966
python main.py list-books
```

Le fichier `library.xml` est mis à jour à chaque opération afin de conserver l'historique des ouvrages et des prêts.

## Interface web de test

Une interface web peut être lancée afin de consulter et enrichir la bibliothèque. Utilisez :

```bash
python main.py serve
```

Ceci démarre le serveur et ouvre automatiquement la page `http://localhost:8000` dans votre navigateur.

