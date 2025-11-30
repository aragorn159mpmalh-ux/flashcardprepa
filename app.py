# app.py
import streamlit as st
import json
import os
import random
import bcrypt

# -----------------------------
# Configuration fichiers
# -----------------------------
USERS_FILE = "users.json"
USER_DATA_DIR = "user_data"  # fichiers {username}.json

os.makedirs(USER_DATA_DIR, exist_ok=True)

# -----------------------------
# Utilitaires utilisateurs & données
# -----------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def safe_filename(username):
    return "".join(c for c in username if c.isalnum() or c in ("_", "-")).strip()

def user_file(username):
    return os.path.join(USER_DATA_DIR, f"{safe_filename(username)}.json")

def load_user_cards(username):
    path = user_file(username)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_cards(username, cards):
    path = user_file(username)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=4, ensure_ascii=False)

# -----------------------------
# Hash & vérification bcrypt
# -----------------------------
def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# -----------------------------
# Session state init
# -----------------------------
if "username" not in st.session_state:
    st.session_state.username = None
if "mode" not in st.session_state:
    st.session_state.mode = "auth"  # auth, menu, create, edit, delete, choose_play, play
if "cards" not in st.session_state:
    st.session_state.cards = {}
if "current_set" not in st.session_state:
    st.session_state.current_set = None
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None

users = load_users()

# -----------------------------
# Auth : register / login / logout
# -----------------------------
def register_page():
    st.header("🆕 Créer un compte")
    username = st.text_input("Nom d'utilisateur", key="reg_user")
    password = st.text_input("Mot de passe", type="password", key="reg_pass")
    if st.button("S'inscrire"):
        if not username or not password:
            st.warning("Remplis les deux champs.")
            return
        if username in users:
            st.error("Ce nom d'utilisateur existe déjà.")
            return
        users[username] = {"password": hash_password(password)}
        save_users(users)
        # créer fichier vide pour l'utilisateur
        save_user_cards(username, {})
        st.success("Compte créé ! Tu peux maintenant te connecter.")

def login_page():
    st.header("🔐 Connexion")
    username = st.text_input("Nom d'utilisateur", key="login_user")
    password = st.text_input("Mot de passe", type="password", key="login_pass")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Se connecter"):
            if not username or not password:
                st.warning("Remplis les deux champs.")
                return
            entry = users.get(username)
            if not entry or "password" not in entry:
                st.error("Identifiants incorrects.")
                return
            if not check_password(password, entry["password"]):
                st.error("Identifiants incorrects.")
                return
            # succès
            st.session_state.username = username
            st.session_state.cards = load_user_cards(username)
            st.session_state.mode = "menu"
            st.success(f"Connecté en tant que {username} !")
    with col2:
        if st.button("Continuer en invité"):
            st.session_state.username = None
            st.session_state.cards = {}
            st.session_state.mode = "menu"
            st.info("Mode invité : aucune modification ne sera sauvegardée.")

def logout():
    st.session_state.username = None
    st.session_state.cards = {}
    st.session_state.mode = "auth"
    for k in ["current_set", "current_mode", "remaining", "current_question", "answer_shown", "total", "score"]:
        if k in st.session_state:
            del st.session_state[k]
    st.experimental_rerun()

# -----------------------------
# Pages : menu / create / edit / delete
# -----------------------------
def menu_page():
    st.title("🧠 Flashcards")
    if st.session_state.username:
        st.write(f"Connecté : **{st.session_state.username}**")
        if st.button("Se déconnecter"):
            logout()
            return
    else:
        st.write("Mode invité (aucune modification ne sera sauvegardée).")

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎓 Réviser une fiche"):
            st.session_state.mode = "choose_play"
    with col2:
        if st.button("➕ Créer une fiche"):
            st.session_state.mode = "create"
    col3, col4 = st.columns(2)
    with col3:
        if st.button("✏️ Modifier une fiche"):
            st.session_state.mode = "choose_edit"
    with col4:
        if st.button("🗑️ Supprimer une fiche"):
            st.session_state.mode = "choose_delete"

    st.write("---")
    if st.session_state.cards:
        st.write("### Tes fiches :")
        for name in st.session_state.cards.keys():
            st.write(f"- {name}")
    else:
        st.info("Tu n'as aucune fiche pour l'instant. Crée-en une !")

def create_page():
    st.title("➕ Créer une nouvelle fiche")
    name = st.text_input("Nom de la fiche", key="create_name")
    text = st.text_area("Cartes (une par ligne, format : question - réponse)", key="create_text", height=200)
    if st.button("Enregistrer la fiche"):
        if not name or not text.strip():
            st.warning("Nom et contenu requis.")
            return
        new_dict = {}
        for line in text.splitlines():
            if "-" in line:
                q, a = line.split("-", 1)
                new_dict[q.strip()] = a.strip()
        if not new_dict:
            st.warning("Aucune carte valide détectée.")
            return
        st.session_state.cards[name] = new_dict
        if st.session_state.username:
            save_user_cards(st.session_state.username, st.session_state.cards)
            st.success("Fiche enregistrée pour ton compte.")
        else:
            st.success("Fiche créée en session invitée (non sauvegardée).")
        st.session_state.mode = "menu"

def choose_edit_page():
    st.title("✏️ Modifier une fiche")
    if not st.session_state.cards:
        st.info("Pas de fiche à modifier.")
        return
    name = st.selectbox("Choisis une fiche :", list(st.session_state.cards.keys()), key="edit_choice")
    if st.button("Modifier cette fiche"):
        st.session_state.editing = name
        st.session_state.mode = "edit"

def edit_page():
    name = st.session_state.get("editing")
    if not name:
        st.warning("Aucune fiche sélectionnée.")
        st.session_state.mode = "menu"
        return
    st.title(f"Modifier : {name}")
    card_map = st.session_state.cards.get(name, {})
    text = "\n".join([f"{q} - {a}" for q,a in card_map.items()])
    edited = st.text_area("Modifie les cartes :", value=text, height=300)
    if st.button("Sauvegarder les modifications"):
        new = {}
        for line in edited.splitlines():
            if "-" in line:
                q,a = line.split("-",1)
                new[q.strip()] = a.strip()
        st.session_state.cards[name] = new
        if st.session_state.username:
            save_user_cards(st.session_state.username, st.session_state.cards)
            st.success("Modifications sauvegardées.")
        else:
            st.success("Modifications appliquées en session (non sauvegardées).")
        st.session_state.mode = "menu"

def choose_delete_page():
    st.title("🗑️ Supprimer une fiche")
    if not st.session_state.cards:
        st.info("Pas de fiche à supprimer.")
        return
    name = st.selectbox("Choisis une fiche :", list(st.session_state.cards.keys()), key="delete_choice")
    if st.button("❌ Supprimer définitivement"):
        st.session_state.cards.pop(name, None)
        if st.session_state.username:
            save_user_cards(st.session_state.username, st.session_state.cards)
        st.success(f"Fiche '{name}' supprimée.")
        st.session_state.mode = "menu"

# -----------------------------
# Play : choix & session (2 modes)
# -----------------------------
def choose_play_page():
    st.title("🎓 Réviser une fiche")
    if not st.session_state.cards:
        st.info("Aucune fiche disponible.")
        return
    name = st.selectbox("Choisis une fiche :", list(st.session_state.cards.keys()), key="play_choice")
    mode = st.radio("Choisis le mode :", ["Écrire la réponse", "Voir la réponse"])
    if st.button("Commencer"):
        st.session_state.current_set = name
        st.session_state.current_mode = mode
        st.session_state.remaining = list(st.session_state.cards[name].keys())
        st.session_state.total = len(st.session_state.remaining)
        st.session_state.current_question = None
        st.session_state.answer_shown = False
        st.session_state.score = 0
        st.session_state.mode = "play"
        st.experimental_rerun()

def play_page():
    name = st.session_state.current_set
    cards = st.session_state.cards[name]

    if not st.session_state.remaining:
        st.success(f"🎉 Fiche '{name}' terminée ! Score : {st.session_state.score}/{st.session_state.total}")
        if st.button("Recommencer"):
            st.session_state.remaining = list(st.session_state.cards[name].keys())
            st.session_state.current_question = None
            st.session_state.answer_shown = False
            st.session_state.score = 0
        if st.button("Retour au menu"):
            st.session_state.mode = "menu"
        return

    if not st.session_state.current_question:
        st.session_state.current_question = random.choice(st.session_state.remaining)

    q = st.session_state.current_question
    a = cards[q]

    st.write(f"### ❓ {q}")

    if st.session_state.current_mode == "Voir la réponse":
        if not st.session_state.answer_shown:
            if st.button("👀 Voir la réponse"):
                st.session_state.answer_shown = True
        else:
            st.info(f"💡 Réponse : {a}")
            col1, col2 = st.columns(2)
            if col1.button("✅ J'ai su"):
                st.session_state.remaining.remove(q)
                st.session_state.current_question = None
                st.session_state.answer_shown = False
                st.session_state.score += 1
            if col2.button("❌ Pas su"):
                st.session_state.current_question = None
                st.session_state.answer_shown = False
    else:
        user = st.text_input("✏️ Ta réponse :", key="answer_input")
        if st.button("Valider"):
            if user.strip().lower() == a.strip().lower():
                st.success("✔️ Correct")
                st.session_state.remaining.remove(q)
                st.session_state.current_question = None
                st.session_state.score += 1
            else:
                st.error(f"❌ Faux — Réponse : {a}")
                st.session_state.current_question = None

    st.info(f"Progression : {st.session_state.total - len(st.session_state.remaining)}/{st.session_state.total}")
    if st.button("Abandonner et retour au menu"):
        st.session_state.mode = "menu"

# -----------------------------
# Sidebar : auth / navigation
# -----------------------------
st.sidebar.title("Compte")
if st.session_state.username:
    st.sidebar.write(f"Connecté : **{st.session_state.username}**")
    if st.sidebar.button("Se déconnecter"):
        logout()
else:
    tab = st.sidebar.radio("Connexion / Inscription", ["Connexion", "Inscription"])
    if tab == "Connexion":
        login_page()
    else:
        register_page()

st.sidebar.write("---")
if st.session_state.username:
    if st.sidebar.button("Menu principal"):
        st.session_state.mode = "menu"

# Router principal
if st.session_state.mode == "auth":
    st.info("Utilise la barre latérale pour te connecter ou t'inscrire.")
elif st.session_state.mode == "menu":
    menu_page()
elif st.session_state.mode == "create":
    create_page()
elif st.session_state.mode == "choose_edit":
    choose_edit_page()
elif st.session_state.mode == "edit":
    edit_page()
elif st.session_state.mode == "choose_delete":
    choose_delete_page()
elif st.session_state.mode == "choose_play":
    choose_play_page()
elif st.session_state.mode == "play":
    play_page()

