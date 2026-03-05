

"""
BGA SCRAPER - Connexion avec cookies persistants
- 1ère fois : tu te connectes manuellement → cookies sauvegardés dans bga_cookies.json
- Fois suivantes : cookies rechargés → connexion automatique sans rien faire
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
import os
from database import DatabaseManager

COOKIES_FILE = "bga_cookies.json"


class BGAScraper:

    def __init__(self, db: DatabaseManager):
        self.db           = db
        self.est_connecte = False

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--user-data-dir=/tmp/chrome-bga")  # ← répertoire dédié
        options.binary_location = "/usr/bin/chromium-browser"

        service = Service("/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=options)
        print("✅ Navigateur Chromium lancé")

    # ==================== COOKIES ====================

    def _save_cookies(self):
        """Sauvegarde les cookies de session dans bga_cookies.json"""
        cookies = self.driver.get_cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f, indent=2)
        print(f"💾 Cookies sauvegardés ({len(cookies)} cookies → {COOKIES_FILE})")

    def _load_cookies(self):
        """Charge les cookies depuis bga_cookies.json et les injecte dans le navigateur"""
        if not os.path.exists(COOKIES_FILE):
            return False
        try:
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
            if not cookies:
                return False
            # Aller sur BGA d'abord (obligatoire avant d'injecter des cookies)
            self.driver.get("https://fr.boardgamearena.com")
            time.sleep(2)
            for cookie in cookies:
                # Supprimer les champs non supportés par Selenium
                cookie.pop("sameSite", None)
                cookie.pop("expiry",   None)
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    pass
            print(f"🍪 {len(cookies)} cookies chargés depuis {COOKIES_FILE}")
            return True
        except Exception as e:
            print(f"⚠️ Erreur chargement cookies : {e}")
            return False

    def _is_logged_in(self):
        """Vérifie si on est bien connecté sur BGA"""
        try:
            current = self.driver.current_url
            title   = self.driver.title
            # Connecté si on n'est pas sur la page login et que le titre contient BGA
            if "login" not in current and "Board Game Arena" in title:
                # Vérification supplémentaire : chercher un élément de l'interface connectée
                try:
                    self.driver.find_element(By.ID, "topbar_connect_controls")
                    return False  # Cet élément = NON connecté
                except Exception:
                    pass
                return True
            return False
        except Exception:
            return False

    # ==================== CONNEXION ====================

    def connecter(self):
        """
        Connexion à BGA avec système de cookies persistants.
        - Si bga_cookies.json existe → connexion automatique
        - Sinon → connexion manuelle une seule fois, cookies sauvegardés
        """
        print("\n" + "="*60)
        print("🔌 CONNEXION À BGA")
        print("="*60)

        # ---- Essai avec les cookies existants ----
        if os.path.exists(COOKIES_FILE):
            print("🍪 Fichier cookies trouvé → tentative connexion automatique...")
            if self._load_cookies():
                # Recharger la page pour appliquer les cookies
                self.driver.get("https://boardgamearena.com")
                time.sleep(3)

                if self._is_logged_in():
                    print("✅ Connexion automatique réussie (cookies valides) !")
                    self.est_connecte = True
                    return True
                else:
                    print("⚠️ Cookies expirés ou invalides → reconnexion manuelle nécessaire")
                    os.remove(COOKIES_FILE)
                    print(f"   Fichier {COOKIES_FILE} supprimé")
            else:
                print("⚠️ Impossible de charger les cookies → connexion manuelle")

        # ---- Connexion manuelle ----
        print("\n" + "-"*60)
        print("📋 CONNEXION MANUELLE (une seule fois)")
        print("-"*60)
        print("1. Le navigateur va s'ouvrir sur la page BGA")
        print("2. Connecte-toi avec ton email et mot de passe")
        print("3. Attends d'être sur la page d'accueil BGA")
        print("4. Reviens ici et appuie sur ENTRÉE")
        print("   ➜ Les cookies seront sauvegardés pour les prochaines fois")
        print("-"*60 + "\n")

        try:
            self.driver.get("https://boardgamearena.com")
            time.sleep(2)

            print("⏳ Connecte-toi dans le navigateur... (le script détecte automatiquement)")
            for i in range(60):  # attend max 2 minutes
                time.sleep(2)
                try:
                    if self._is_logged_in():
                        print("✅ Connexion détectée !")
                        break
                    else:
                        print(f"   En attente... ({(i+1)*2}s)", end="\r")
                except Exception:
                    print("❌ Navigateur fermé pendant l'attente")
                    return False

            time.sleep(2)
            current = self.driver.current_url
            title   = self.driver.title
            print(f"\n   URL   : {current}")
            print(f"   Titre : {title}")

            if "login" in current.lower():
                print("❌ Toujours sur la page login. Vérifie tes identifiants et réessaie.")
                self.est_connecte = False
                return False

            if "Board Game Arena" in title or "boardgamearena" in current:
                # Sauvegarder les cookies pour les prochaines fois
                self._save_cookies()
                print("✅ Connexion manuelle réussie !")
                print(f"💡 Prochaine fois : connexion automatique via {COOKIES_FILE}")
                self.est_connecte = True
                return True
            else:
                print("❌ Connexion non détectée. Réessaie.")
                self.est_connecte = False
                return False

        except Exception as e:
            print(f"❌ Erreur : {e}")
            self.est_connecte = False
            return False

    # ==================== SCRAPING PARTIES ====================

    def get_parties_joueur(self, bga_pseudo, nb_parties=50):
        if not self.est_connecte:
            print("❌ Non connecté")
            return []

        print(f"\n🔍 Récupération des parties de '{bga_pseudo}'...")

        try:
            import re
            player_id = None

            # ── MÉTHODE 1 : page de recherche communautaire ──────────────────
            search_url = f"https://en.boardgamearena.com/community/players?query={bga_pseudo}"
            print(f"   → GET {search_url}")
            self.driver.get(search_url)
            time.sleep(3)

            src = self.driver.page_source
            for pattern in [r'/player\?id=(\d+)', r'"id"\s*:\s*"?(\d+)"?', r'player_id["\s:=]+(\d+)']:
                m = re.search(pattern, src)
                if m:
                    player_id = m.group(1)
                    print(f"   ✅ ID trouvé : {player_id}")
                    break

            # ── MÉTHODE 2 : page profil par pseudo ───────────────────────────
            if not player_id:
                profile_url = f"https://en.boardgamearena.com/player?title={bga_pseudo}"
                print(f"   → GET {profile_url}")
                self.driver.get(profile_url)
                time.sleep(3)

                cur = self.driver.current_url
                if "id=" in cur:
                    player_id = cur.split("id=")[1].split("&")[0]
                    print(f"   ✅ ID trouvé dans l'URL : {player_id}")
                else:
                    src = self.driver.page_source
                    for pattern in [r'/player\?id=(\d+)', r'"id"\s*:\s*"?(\d+)"?']:
                        m = re.search(pattern, src)
                        if m:
                            player_id = m.group(1)
                            print(f"   ✅ ID trouvé dans le HTML : {player_id}")
                            break

            if not player_id:
                print("❌ Impossible de trouver l'ID du joueur.")
                return []

            print(f"\n   🎯 ID joueur final : {player_id}")

            # ── Passage par l'accueil pour activer la session ─────────────────
            print("   → Passage par l'accueil...")
            self.driver.get("https://boardgamearena.com/")
            time.sleep(3)

            # ── Appel API via fetch JS (cookies automatiques) ─────────────────
            api_path = f"/gamestats/gamestats/getgames.html?player={player_id}&game_id=0&start=0&count={nb_parties}&updatetype=normal"
            print(f"   → fetch JS : {api_path}")

            result = self.driver.execute_script(f"""
                const response = await fetch('{api_path}', {{
                    method: 'GET',
                    credentials: 'include'
                }});
                return await response.text();
            """)

            print(f"   Réponse brute (200 chars) : {result[:200]}")

            data   = json.loads(result)
            tables = data.get("data", {}).get("tables", [])
            cf     = [t for t in tables if t.get("game_name") == "connectfour"]
            print(f"✅ {len(cf)} parties Connect Four trouvées")
            return [t["table_id"] for t in cf]

        except json.JSONDecodeError as e:
            print(f"❌ JSON invalide : {e}")
            return []
        except Exception as e:
            import traceback
            print(f"❌ Erreur : {e}")
            traceback.print_exc()
            return []

    def inserer_partie_bga(self, infos):
        """Insère une partie BGA dans la BDD"""
        if not infos or not infos.get("sequence"):
            return "error"

        j1 = self.db.get_or_create_joueur(infos["joueur1"])
        j2 = self.db.get_or_create_joueur(infos["joueur2"])

        gagnant_id = None
        if infos["gagnant"] == infos["joueur1"]:   gagnant_id = j1
        elif infos["gagnant"] == infos["joueur2"]: gagnant_id = j2

        result = self.db.import_partie_from_sequence(
            sequence=infos["sequence"],
            joueur1_id=j1, joueur2_id=j2,
            nb_colonnes=7
        )

        if result["status"] == "created":
            try:
                cur = self.db.connection.cursor()
                cur.execute(
                    "UPDATE parties SET source='bga', bga_game_id=%s, bga_url=%s WHERE id=%s",
                    (infos["table_id"], infos["bga_url"], result["partie_id"])
                )
                self.db.connection.commit()
                cur.close()
            except Exception:
                pass

        return result["status"]

    def scraper_joueur(self, bga_pseudo, nb_parties=50, delai=1.5):
        """Scrape toutes les parties Connect Four d'un joueur BGA"""
        if not self.est_connecte:
            print("❌ Non connecté")
            return {}

        stats = {"total": 0, "creees": 0, "doublons": 0, "symetriques": 0, "erreurs": 0}
        ids   = self.get_parties_joueur(bga_pseudo, nb_parties)

        if not ids:
            print("⚠️ Aucune partie trouvée")
            return stats

        stats["total"] = len(ids)
        print(f"\n📥 Traitement de {len(ids)} parties...\n")

        for i, tid in enumerate(ids):
            print(f"[{i+1}/{len(ids)}] Table {tid}... ", end="", flush=True)
            infos  = self.get_sequence_partie(tid)
            if not infos:
                print("❌"); stats["erreurs"] += 1
            else:
                status = self.inserer_partie_bga(infos)
                if   status == "created":    print(f"✅ {infos['sequence'][:10]}..."); stats["creees"] += 1
                elif status == "exists":     print("⏭️  Doublon");                     stats["doublons"] += 1
                elif status == "symetrique": print("🔄 Symétrique");                   stats["symetriques"] += 1
                else:                        print("❌ Erreur");                        stats["erreurs"] += 1
            time.sleep(delai)

        print("\n" + "="*50)
        print(f"  ✅ Créées      : {stats['creees']}")
        print(f"  ⏭️  Doublons    : {stats['doublons']}")
        print(f"  🔄 Symétriques : {stats['symetriques']}")
        print(f"  ❌ Erreurs     : {stats['erreurs']}")
        print("="*50)
        return stats

    def fermer(self):
        try:
            self.driver.quit()
            print("🔒 Navigateur fermé")
        except Exception:
            pass


# ==================== MAIN ====================

if __name__ == "__main__":
    db = DatabaseManager(
        host="localhost", user="root",
        password="Admin@123456", database="puissance4"
    )
    db.connect()

    scraper = BGAScraper(db)
    pseudo  = input("👤 Pseudo BGA à scraper : ")

    if scraper.connecter():
        scraper.scraper_joueur(bga_pseudo=pseudo, nb_parties=100, delai=1.5)

    scraper.fermer()
    db.disconnect()

    if scraper.connecter():
        scraper.scraper_joueur(bga_pseudo=pseudo, nb_parties=100, delai=1.5)

    input("⏳ Appuie sur ENTRÉE pour fermer...")  # ← ajoute ici
    scraper.fermer()
