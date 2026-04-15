import streamlit as st
import pandas as pd
import unicodedata
import difflib
import io

# --- CLASSE DE COMPARAISON ---
class CSVComparer:
    def __init__(self, seuil_similarite=0.85):
        self.seuil_similarite = seuil_similarite

    def normaliser_texte(self, texte):
        if pd.isna(texte): return ""
        texte = str(texte).lower().strip()
        texte = " ".join(texte.split())
        texte = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
        return texte

    def comparer_deux_df(self, df1, df2, colonne1, colonne2):
        liste1_nettoyee = df1[colonne1].apply(self.normaliser_texte).tolist()
        liste2_nettoyee = df2[colonne2].apply(self.normaliser_texte).tolist()

        resultats = []
        for original_val in df1[colonne1]:
            val_nettoyee = self.normaliser_texte(original_val)
            if val_nettoyee in liste2_nettoyee:
                resultats.append({'Valeur_Fichier_1': original_val, 'Correspondance': 'Exacte', 'Valeur_Trouvee_Fichier_2': original_val, 'Score': "100%"})
            else:
                matches = difflib.get_close_matches(val_nettoyee, liste2_nettoyee, n=1, cutoff=self.seuil_similarite)
                if matches:
                    match_nettoye = matches[0]
                    idx_match = liste2_nettoyee.index(match_nettoye)
                    val_originale_2 = df2.iloc[idx_match][colonne2]
                    score = difflib.SequenceMatcher(None, val_nettoyee, match_nettoye).ratio()
                    resultats.append({'Valeur_Fichier_1': original_val, 'Correspondance': 'Approximative', 'Valeur_Trouvee_Fichier_2': val_originale_2, 'Score': f"{round(score * 100, 2)}%"})
                else:
                    resultats.append({'Valeur_Fichier_1': original_val, 'Correspondance': 'Aucune', 'Valeur_Trouvee_Fichier_2': 'N/A', 'Score': '0%'})
        
        return pd.DataFrame(resultats)

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Data Cleaner", layout="wide")
st.title("🔍 Comparateur de Données & Fuzzy Matching")
st.write("Identifiez les correspondances exactes et approximatives entre deux fichiers.")

# Configuration du curseur de similarité
seuil = st.slider("Seuil de tolérance (Fuzzy Matching)", min_value=0.50, max_value=1.00, value=0.85, step=0.01)

col1, col2 = st.columns(2)

with col1:
    fichier1 = st.file_uploader("📂 Charger le Fichier 1 (Excel ou CSV)", type=['csv', 'xlsx'])
with col2:
    fichier2 = st.file_uploader("📂 Charger le Fichier 2 (Excel ou CSV)", type=['csv', 'xlsx'])

if fichier1 and fichier2:
    # Lecture des fichiers
    df1 = pd.read_excel(fichier1) if fichier1.name.endswith('xlsx') else pd.read_csv(fichier1)
    df2 = pd.read_excel(fichier2) if fichier2.name.endswith('xlsx') else pd.read_csv(fichier2)

    # Sélection dynamique des colonnes
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        colonne1 = st.selectbox("📌 Colonne à analyser (Fichier 1)", df1.columns)
    with col_sel2:
        colonne2 = st.selectbox("📌 Colonne de référence (Fichier 2)", df2.columns)

    # Lancement
    if st.button("🚀 Lancer la comparaison", type="primary"):
        with st.spinner("Analyse en cours..."):
            comparateur = CSVComparer(seuil_similarite=seuil)
            df_resultat = comparateur.comparer_deux_df(df1, df2, colonne1, colonne2)
            
            st.success("Comparaison terminée !")
            st.dataframe(df_resultat) # Affichage du résultat
            
            # Création du fichier Excel en mémoire pour le téléchargement
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_resultat.to_excel(writer, index=False, sheet_name='Résultats')
            
            st.download_button(
                label="📥 Télécharger le rapport Excel",
                data=buffer.getvalue(),
                file_name="Rapport_Comparaison.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )