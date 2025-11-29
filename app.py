import streamlit as st
import json
import os
import random

# -----------------------------
# Chargement & sauvegarde JSON
# -----------------------------
CARDS_FILE = "flashcards.json"

DEFAULT_CARDS = {
    "mot pour synthese": {
        "le dernier cité": "The latter",
        "to weight up": "évaluer, peser le pour et le contre",
        "to enhance": "améliorer",
        "so called": "soi-disant",
        "namely": "à savoir, en l'occurrence"
    },
    "lien logique": {
        "thus": "ainsi",
        "while": "tandis que",
        "Hence": "d'où",
        "wether it be": "qu'il s'agisse de"
    },
    "grammaire": {
        "Avoir l'habitude de": "to be used to + v en ing",
        "action révolue : avant mais plus maintenant": "used to + BV",
        "depuis": "for (durée) / since (point de départ)",
        "exprimer une date limite (prêt d'ici demain)": "by (ready by tomorrow)",
        "moi aussi": "so + auxiliaire (She has finished, so have I)"
    }
}

def load_json():
    if not os.path.exists(CARDS_FILE):
        save_json(DEFAULT_CARDS)
        return DEFAULT_CARDS
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data):
    with open(CARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

CARDS = load_json()

# -----------------------------
# App Streamlit
# -----------------------------
st.title("🧠 Flashcards Online")

menu = st.sidebar.selectbox(
    "Menu",
    ["🏠 Accueil", "🎓 Réviser une fiche", "➕ Créer une fiche",
     "✏️ Modifier une fiche", "🗑️ Supprimer une fiche"]
)

# -----------------------------
# ACCUEIL
# -----------------------------
if menu == "🏠 Accueil":
    st.subheader("Bienvenue dans ton application de Flashcards !")
    st.write("Choisis une action dans le menu à gauche.")

# -----------------------------
# CRÉER UNE FICHE
# -----------------------------
elif menu == "➕ Créer une fiche":
    st.subheader("Créer une nouvelle fiche")

    name = st.text_input("Nom de la fiche")

    content = st.text_area(
        "Ajoute tes cartes (une par ligne, format : question - réponse)"
    )

    if st.button("Enregistrer"):
        if name.strip() == "" or content.strip() == "":
            st.warning("Remplis tous les champs.")
        else:
            new_cards = {}
            for line in content.split("\n"):
                if "-" in line:
                    q, a = line.split("-", 1)
                    new_cards[q.strip()] = a.strip()
            CARDS[name] = new_cards
            save_json(CARDS)
            st.success(f"Fiche '{name}' créée avec succès !")

# -----------------------------
# MODIFIER UNE FICHE
# -----------------------------
elif menu == "✏️ Modifier une fiche":
    st.subheader("Modifier une fiche")

    chosen = st.selectbox("Choisis une fiche :", list(CARDS.keys()))

    existing = CARDS[chosen]
    text = "\n".join([f"{q} - {a}" for q, a in existing.items()])

    edited = st.text_area("Modifie les cartes :", text)

    if st.button("Enregistrer les modifications"):
        new_cards = {}
        for line in edited.split("\n"):
            if "-" in line:
                q, a = line.split("-", 1)
                new_cards[q.strip()] = a.strip()
        CARDS[chosen] = new_cards
        save_json(CARDS)
        st.success("Modifications enregistrées.")

# -----------------------------
# SUPPRIMER UNE FICHE
# -----------------------------
elif menu == "🗑️ Supprimer une fiche":
    st.subheader("Supprimer une fiche")
    chosen = st.selectbox("Sélectionne une fiche :", list(CARDS.keys()))

    if st.button("Supprimer définitivement"):
        CARDS.pop(chosen)
        save_json(CARDS)
        st.success(f"Fiche '{chosen}' supprimée.")

# -----------------------------
# RÉVISER UNE FICHE
# -----------------------------
elif menu == "🎓 Réviser une fiche":
    st.subheader("Choisis une fiche à réviser")

    list_name = st.selectbox("Fiche :", list(CARDS.keys()))
    mode = st.radio("Choisis ton mode :", ["✍️ Mode écriture", "👀 Mode affichage simple"])

    if st.button("Commencer"):
        st.session_state["flash_list"] = list_name
        st.session_state["mode"] = mode
        st.session_state["remaining"] = list(CARDS[list_name].keys())
        st.session_state["current"] = None
        st.session_state["score"] = 0

    # Déjà une session lancée ?
    if "remaining" in st.session_state and st.session_state.get("flash_list") == list_name:
        remaining = st.session_state["remaining"]

        if len(remaining) == 0:
            st.success("🎉 Fiche terminée !")
            st.write(f"Score : {st.session_state['score']}")
            if st.button("Recommencer"):
                st.session_state["remaining"] = list(CARDS[list_name].keys())
                st.session_state["score"] = 0
            st.stop()

        # Nouvelle carte ?
        if st.session_state["current"] is None:
            st.session_state["current"] = random.choice(remaining)

        q = st.session_state["current"]
        a = CARDS[list_name][q]

        st.write(f"### ❓ {q}")

        mode = st.session_state["mode"]

        # Mode écriture
        if mode == "✍️ Mode écriture":
            user = st.text_input("Écris ta réponse")

            if st.button("Valider"):
                if user.lower().strip() == a.lower().strip():
                    st.success("✔ Correct !")
                    st.session_state["score"] += 1
                    remaining.remove(q)
                    st.session_state["current"] = None
                else:
                    st.error(f"❌ Incorrect. Réponse : {a}")

        # Mode affichage simple
        else:
            if st.button("Voir la réponse"):
                st.info(f"💡 Réponse : {a}")

            col1, col2 = st.columns(2)
            if col1.button("J'ai su"):
                st.session_state["score"] += 1
                remaining.remove(q)
                st.session_state["current"] = None
            if col2.button("Pas su"):
                st.session_state["current"] = None
