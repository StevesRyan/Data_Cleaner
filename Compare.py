import pandas as pd
import unicodedata
import difflib

class CSVComparer:
    def __init__(self, seuil_similarite=0.85):
        """
        seuil_similarite: définit à partir de quel pourcentage (0.85 = 85%) 
        on considère que deux noms différents sont en fait les mêmes.
        """
        self.seuil_similarite = seuil_similarite

    def normaliser_texte(self, texte):
        """
        Nettoie le texte : gère la casse, les accents et les espaces.
        Ex: " HÔPITAL   Central " -> "hopital central"
        """
        if pd.isna(texte):
            return ""
        
        # 1. Convertir en texte, minuscules et enlever les espaces aux extrémités
        texte = str(texte).lower().strip()
        
        # 2. Remplacer les espaces multiples par un seul espace
        texte = " ".join(texte.split())
        
        # 3. Enlever les accents
        texte = ''.join(c for c in unicodedata.normalize('NFD', texte) 
                        if unicodedata.category(c) != 'Mn')
        return texte

    def trouver_doublons_internes(self, df, colonne):
        """Trouve les doublons dans un seul fichier CSV."""
        print(f"\n--- Recherche de doublons dans la colonne '{colonne}' ---")
        df['texte_nettoye'] = df[colonne].apply(self.normaliser_texte)
        
        # Trouver les doublons stricts après nettoyage
        doublons = df[df.duplicated(subset=['texte_nettoye'], keep=False)]
        
        if not doublons.empty:
            print(f"⚠️ {len(doublons)} doublons trouvés (après nettoyage de la casse/accents) :")
            for _, row in doublons.iterrows():
                print(f" - {row[colonne]}")
        else:
            print("✅ Aucun doublon interne trouvé.")
            
        return doublons

    def comparer_deux_csv(self, fichier1, fichier2, colonne1, colonne2):
        """Compare deux fichiers CSV ou Excel et trouve les correspondances exactes et approximatives."""
        # Charger les fichiers (CSV ou Excel)
        df1 = pd.read_excel(fichier1) if fichier1.endswith(('.xls', '.xlsx')) else pd.read_csv(fichier1)
        df2 = pd.read_excel(fichier2) if fichier2.endswith(('.xls', '.xlsx')) else pd.read_csv(fichier2)

        # Eliminer les espaces inutiles dans les noms des colonnes
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # Nettoyer les colonnes
        liste1_nettoyee = df1[colonne1].apply(self.normaliser_texte).tolist()
        liste2_nettoyee = df2[colonne2].apply(self.normaliser_texte).tolist()

        resultats = []

        for original_val in df1[colonne1]:
            val_nettoyee = self.normaliser_texte(original_val)
            
            # 1. Recherche d'une correspondance EXACTE (après nettoyage)
            if val_nettoyee in liste2_nettoyee:
                resultats.append({
                    'Valeur_Fichier_1': original_val,
                    'Correspondance': 'Exacte',
                    'Valeur_Trouvee_Fichier_2': original_val, # Simplifié
                    'Score': "100%"
                })
            else:
                # 2. Recherche d'une correspondance APPROXIMATIVE (Fuzzy Matching)
                matches = difflib.get_close_matches(
                    val_nettoyee, liste2_nettoyee, n=1, cutoff=self.seuil_similarite
                )
                
                if matches:
                    match_nettoye = matches[0]
                    # Retrouver la valeur originale dans le DF2 correspondant à ce nettoyage
                    idx_match = liste2_nettoyee.index(match_nettoye)
                    val_originale_2 = df2.iloc[idx_match][colonne2]
                    
                    score = difflib.SequenceMatcher(None, val_nettoyee, match_nettoye).ratio()
                    
                    resultats.append({
                        'Valeur_Fichier_1': original_val,
                        'Correspondance': 'Approximative',
                        'Valeur_Trouvee_Fichier_2': val_originale_2,
                        'Score': f"{round(score * 100, 2)}%"
                    })
                else:
                    resultats.append({
                        'Valeur_Fichier_1': original_val,
                        'Correspondance': 'Aucune',
                        'Valeur_Trouvee_Fichier_2': 'N/A',
                        'Score': '0%'
                    })

        # Créer un rapport final
        df_rapport = pd.DataFrame(resultats)
        df_rapport.to_csv("rapport_comparaison.csv", index=False)
        print("\n✅ Comparaison terminée ! Rapport sauvegardé dans 'rapport_comparaison.csv'")
        return df_rapport

# ==========================================
# EXEMPLE D'UTILISATION (Réutilisable)
# ==========================================
if __name__ == "__main__":
    comparateur = CSVComparer(seuil_similarite=0.85) # 85% de ressemblance minimum
    
    # Pour tester les doublons internes d'un CSV (Décommentez si besoin)
    df_test = pd.read_excel("Hopitaux_Galilee.xlsx")
    print("Voici les colonnes trouvées par Python :", df_test.columns.tolist()) 
    comparateur.trouver_doublons_internes(df_test, "Liste des centres conventionnés")

    # Pour comparer deux fichiers :
    #comparateur.comparer_deux_csv("Hopitaux_Galilee.xlsx", "Hopitaux_ORASS.xlsx", "Liste des centres conventionnés", "Intitulé")