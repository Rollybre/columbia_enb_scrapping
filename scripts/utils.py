import pandas as pd
import os
import re

def csv_to_txt(csv_file, col_name, col_name_title, outptput_dir, verbose=False): 
    """
    Convertit les colonnes d'un fichier CSV en fichiers texte individuels.

    Args:
        csv_file (str): Chemin vers le fichier CSV.
        col_name (str): Nom de la colonne contenant le contenu à écrire dans les fichiers texte.
        col_name_title (str): Nom de la colonne contenant les titres (utilisés comme noms de fichiers).
        outptput_dir (str): Répertoire où les fichiers texte seront sauvegardés.
        verbose (bool): Si True, affiche des messages de log.

    Returns:
        None
    """
    # Charger le fichier CSV
    df = pd.read_csv(csv_file)
    contents = df[col_name]
    titles = df[col_name_title]

    # Créer le répertoire de sortie s'il n'existe pas
    if not os.path.exists(outptput_dir):
        os.makedirs(outptput_dir)

    # Parcourir les contenus et les titres
    for content, title in zip(contents, titles): 
        # Nettoyer le titre pour éviter les caractères non valides
        safe_title = re.sub(r'[<>:"/\\|?\s,*]', '_', title)
        outptput_path = os.path.join(outptput_dir, f"{safe_title}.txt")

        # Écrire le contenu dans un fichier texte
        with open(outptput_path, mode='w', encoding='utf-8') as f: 
            f.write(content)
        
        if verbose:
            print(f'Text file saved at {outptput_path}')
    return 


