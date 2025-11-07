"""
Application Streamlit avec interface React iOS-like intégrée.
"""

import os
# Fix pour OpenMP sur macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
torch.set_num_threads(1)

import streamlit as st
import subprocess
import sys
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Mon IA Média",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS pour masquer les éléments Streamlit par défaut
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        padding: 0;
        margin: 0;
    }
    .stApp > header {
        padding: 0;
    }
    .stApp > div {
        padding: 0;
    }
    iframe {
        border: none;
        width: 100%;
        height: 100vh;
    }
</style>
""", unsafe_allow_html=True)

def check_dependencies():
    """Vérifie que les dépendances sont installées."""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        return False

def install_dependencies():
    """Installe les dépendances manquantes."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'installation: {e}")
        return False

def start_api_server():
    """Démarre le serveur API Flask en arrière-plan."""
    try:
        # Utiliser le port 5001 par défaut (5000 est souvent utilisé par AirPlay sur macOS)
        api_port = int(os.environ.get('FLASK_PORT', 5001))
        
        # Vérifier si le serveur est déjà en cours d'exécution
        import requests
        try:
            response = requests.get(f"http://localhost:{api_port}/api/health", timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        
        # Démarrer le serveur
        api_script = Path(__file__).parent / "api_server.py"
        if api_script.exists():
            # Lancer le serveur en arrière-plan
            process = subprocess.Popen(
                [sys.executable, str(api_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Attendre un peu pour que le serveur démarre
            import time
            time.sleep(2)
            return True
        else:
            st.error("Fichier api_server.py introuvable")
            return False
    except Exception as e:
        st.error(f"Erreur lors du démarrage du serveur API: {e}")
        return False

def main():
    """Fonction principale."""
    st.title("Mon IA Média")
    
    # Vérifier les dépendances
    if not check_dependencies():
        st.warning("⚠️  Dépendances manquantes (Flask, Flask-CORS)")
        if st.button("Installer les dépendances"):
            if install_dependencies():
                st.success("✅ Dépendances installées! Rechargez la page.")
                st.rerun()
            else:
                st.error("❌ Erreur lors de l'installation")
        return
    
    # Démarrer le serveur API
    if 'api_started' not in st.session_state:
        with st.spinner("Démarrage du serveur API..."):
            if start_api_server():
                st.session_state.api_started = True
                st.success("✅ Serveur API démarré")
            else:
                st.error("❌ Impossible de démarrer le serveur API")
                return
    
    # Vérifier si l'interface React est construite
    dist_dir = Path(__file__).parent / "dist"
    index_html = dist_dir / "index.html"
    
    if not index_html.exists():
        st.warning("⚠️  Interface React non construite")
        st.info("""
        Pour construire l'interface React:
        1. Installez les dépendances: `npm install`
        2. Construisez l'application: `npm run build`
        3. Rechargez cette page
        """)
        
        if st.button("Construire l'interface React"):
            with st.spinner("Construction de l'interface React..."):
                try:
                    # Vérifier si npm est disponible
                    subprocess.check_call(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Installer les dépendances
                    subprocess.check_call(["npm", "install"], cwd=Path(__file__).parent)
                    
                    # Construire l'application
                    subprocess.check_call(["npm", "run", "build"], cwd=Path(__file__).parent)
                    
                    st.success("✅ Interface React construite! Rechargez la page.")
                    st.rerun()
                except subprocess.CalledProcessError as e:
                    st.error(f"❌ Erreur lors de la construction: {e}")
                except FileNotFoundError:
                    st.error("❌ npm n'est pas installé. Installez Node.js et npm.")
        return
    
    # Afficher l'interface React
    try:
        # Lire le fichier HTML
        with open(index_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Modifier les chemins pour qu'ils pointent vers le bon répertoire
        html_content = html_content.replace(
            'src="/',
            'src="/dist/'
        ).replace(
            'href="/',
            'href="/dist/'
        )
        
        # Afficher l'interface
        st.components.v1.html(html_content, height=800, scrolling=True)
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de l'interface: {e}")
        st.code(str(e))

if __name__ == "__main__":
    main()

