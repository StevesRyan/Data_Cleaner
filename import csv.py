from zk import ZK
import csv

# --- CONFIGURATION ---
ADRESSE_IP = '192.168.1.237'  # <--- Remplace par l'IP de TA badgeuse
PORT = 4370                   # Port standard ZK
# ---------------------

def extraire_donnees_reseau():
    zk = ZK(ADRESSE_IP, port=PORT, timeout=5, force_udp=False)
    conn = None
    
    try:
        print(f"📡 Tentative de connexion à la badgeuse ({ADRESSE_IP})...")
        conn = zk.connect()
        
        # Désactiver les bips pendant l'extraction (optionnel)
        conn.disable_device()
        
        print("📥 Récupération des pointages en cours...")
        attendance = conn.get_attendance()
        
        if attendance:
            fichier_csv = "pointages_badgeuse.csv"
            with open(fichier_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID_Employe', 'Date_Heure', 'Statut', 'Methode'])
                
                for record in attendance:
                    # record.user_id : ID de l'employé
                    # record.timestamp : Objet datetime
                    # record.status : 0 pour entrée, 1 pour sortie (généralement)
                    writer.writerow([record.user_id, record.timestamp, record.status, record.punch])
            
            print(f"✅ Succès ! {len(attendance)} enregistrements sauvegardés dans {fichier_csv}")
        else:
            print("ℹ️ La badgeuse est vide ou aucun pointage n'a été trouvé.")

        # Réactiver la badgeuse
        conn.enable_device()
        
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        print("\nConseils :")
        print(f"1. Vérifie que ton PC est sur le même réseau que la badgeuse ({ADRESSE_IP}).")
        print("2. Teste un 'ping " + ADRESSE_IP + "' dans ton terminal.")
        print("3. Vérifie dans les menus de la badgeuse que le port 4370 est ouvert.")
        
    finally:
        if conn:
            conn.disconnect()
            print("🔌 Déconnecté.")

if __name__ == "__main__":
    extraire_donnees_reseau()