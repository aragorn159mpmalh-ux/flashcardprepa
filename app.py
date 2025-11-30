import streamlit as st
import json
import os
import random


# -----------------------------
# Fichiers JSON
# -----------------------------
CARDS_FILE = "flashcards.json"
DEFAULT_CARDS = {}


def load_json(filename):
    """Charge les fiches depuis un fichier JSON et fusionne avec les fiches par défaut."""
    data = DEFAULT_CARDS.copy()
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                for name, cards in file_data.items():
                    data[name] = cards
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
    return data


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# Load & Session State
if "cards" not in st.session_state:
    st.session_state.cards = load_json(CARDS_FILE)

if "mode" not in st.session_state:
    st.session_state.mode = "menu"  # menu, play, create, edit, delete


# ---------------------------------------------------
# PAGE : MENU PRINCIPAL
# ---------------------------------------------------
def menu_page():
    st.title("🧠 Flashcards")

    st.write("### Choisis une action :")

    if st.button("🎓 Lancer une fiche"):
        st.session_state.mode = "choose_play"

    if st.button("➕ Créer une nouvelle fiche"):
        st.session_state.mode = "create"

    if st.button("✏️ Modifier une fiche"):
        st.session_state.mode = "choose_edit"

    if st.button("🗑️ Supprimer une fiche"):
        st.session_state.mode = "choose_delete"


# ---------------------------------------------------
# PAGE : CHOIX DE LA FICHE À LANCER
# ---------------------------------------------------
def choose_play_page():
    st.title("🎓 Lancer une fiche")

    cards = st.session_state.cards

    name = st.selectbox("Choisis une fiche :", list(cards.keys()))

    mode = st.radio("Choisis le mode :", ["Mode Révision (voir la réponse)", "Mode Saisie (écrire la réponse)"])

    if st.button("▶️ Lancer"):
        st.session_state.current_set = name
        st.session_state.current_mode = mode
        st.session_state.mode = "play"
        start_session()


# ---------------------------------------------------
# LANCEMENT DE SESSION FLASHCARDS
# ---------------------------------------------------
def start_session():
    name = st.session_state.current_set
    cards = st.session_state.cards[name]

    if "remaining" not in st.session_state:
        st.session_state.remaining = list(cards.keys())
        st.session_state.score = 0
        st.session_state.total = len(cards)
        st.session_state.current_question = None
        st.session_state.answer_shown = False

    # Fin ?
    if not st.session_state.remaining:
        st.success(f"🎉 Tu as terminé la fiche **{name}** !")
        if st.button("🔄 Rejouer"):
            del st.session_state.remaining
            st.session_state.mode = "play"
        if st.button("🏠 Retour au menu"):
            reset_session()
            st.session_state.mode = "menu"
        return

    # Nouvelle question ?
    if st.session_state.current_question is None:
        st.session_state.current_question = random.choice(st.session_state.remaining)

    question = st.session_state.current_question
    answer = cards[question]

    st.title(f"📘 {name}")
    st.write(f"### ❓ {question}")

    # Mode 1 : Voir la réponse
    if st.session_state.current_mode == "Mode Révision (voir la réponse)":
        if not st.session_state.answer_shown:
            if st.button("👀 Voir la réponse"):
                st.session_state.answer_shown = True
        else:
            st.success(f"💡 Réponse : {answer}")
            col1, col2 = st.columns(2)
            if col1.button("✅ J'ai su"):
                st.session_state.remaining.remove(question)
                st.session_state.current_question = None
                st.session_state.answer_shown = False
            if col2.button("❌ Pas su"):
                st.session_state.current_question = None
                st.session_state.answer_shown = False

    # Mode 2 : Écrire la réponse
    else:
        user_answer = st.text_input("✏️ Ta réponse :")

        if st.button("Valider"):
            if user_answer.strip().lower() == answer.strip().lower():
                st.success("✅ Bonne réponse !")
                st.session_state.remaining.remove(question)
            else:
                st.error(f"❌ Faux ! La bonne réponse était : {answer}")

            st.session_state.current_question = None

    # Progression
    done = st.session_state.total - len(st.session_state.remaining)
    st.info(f"Progression : {done}/{st.session_state.total}")

    if st.button("🏠 Retour au menu"):
        reset_session()
        st.session_state.mode = "menu"


def reset_session():
    for key in ["remaining", "current_question", "score", "total", "answer_shown"]:
        if key in st.session_state:
            del st.session_state[key]


# ---------------------------------------------------
# PAGE : CRÉATION D’UNE FICHE
# ---------------------------------------------------
def create_page():
    st.title("➕ Créer une nouvelle fiche")

    name = st.text_input("Nom de la fiche")

    text = st.text_area("Questions - Réponses (une par ligne, format : question - réponse)")

    if st.button("💾 Enregistrer"):
        if not name or not text.strip():
            st.warning("Remplis tous les champs.")
            return

        new_dict = {}
        for line in text.split("\n"):
            if "-" in line:
                q, a = line.split("-", 1)
                new_dict[q.strip()] = a.strip()

        if not new_dict:
            st.warning("Aucune carte valide.")
            return

        st.session_state.cards[name] = new_dict
        save_json(CARDS_FILE, st.session_state.cards)
        st.success(f"Fiche '{name}' enregistrée !")
        st.session_state.mode = "menu"


# ---------------------------------------------------
# PAGE : CHOISIR UNE FICHE À MODIFIER
# ---------------------------------------------------
def choose_edit_page():
    st.title("✏️ Modifier une fiche")
    name = st.selectbox("Choisis une fiche :", list(st.session_state.cards.keys()))

    if st.button("Modifier"):
        st.session_state.editing = name
        st.session_state.mode = "edit"


# ---------------------------------------------------
# PAGE : ÉDITION D’UNE FICHE
# ---------------------------------------------------
def edit_page():
    name = st.session_state.editing
    st.title(f"Modifier : {name}")

    cards = st.session_state.cards[name]

    text = ""
    for q, a in cards.items():
        text += f"{q} - {a}\n"

    new_text = st.text_area("Modifie les cartes :", text)

    if st.button("💾 Sauvegarder"):
        new_dict = {}
        for line in new_text.split("\n"):
            if "-" in line:
                q, a = line.split("-", 1)
                new_dict[q.strip()] = a.strip()

        st.session_state.cards[name] = new_dict
        save_json(CARDS_FILE, st.session_state.cards)
        st.success("Modifications enregistrées !")
        st.session_state.mode = "menu"


# ---------------------------------------------------
# PAGE : SUPPRESSION
# ---------------------------------------------------
def choose_delete_page():
    st.title("🗑️ Supprimer une fiche")
    name = st.selectbox("Choisis une fiche :", list(st.session_state.cards.keys()))

    if st.button("❌ Supprimer définitivement"):
        del st.session_state.cards[name]
        save_json(CARDS_FILE, st.session_state.cards)
        st.success(f"Fiche '{name}' supprimée.")
        st.session_state.mode = "menu"


# ---------------------------------------------------
# ROUTEUR PRINCIPAL
# ---------------------------------------------------
if st.session_state.mode == "menu":
    menu_page()

elif st.session_state.mode == "choose_play":
    choose_play_page()

elif st.session_state.mode == "play":
    start_session()

elif st.session_state.mode == "create":
    create_page()

elif st.session_state.mode == "choose_edit":
    choose_edit_page()

elif st.session_state.mode == "edit":
    edit_page()

elif st.session_state.mode == "choose_delete":
    choose_delete_page()


