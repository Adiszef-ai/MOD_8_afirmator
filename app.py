import streamlit as st
import base64
from openai import OpenAI
# from dotenv import dotenv_values

# --------------------------
# Stałe i konfiguracja
# --------------------------

VOICE_OPTIONS = {
    "Jasny syntetyczny": "alloy",
    "Głęboki dramatyczny": "echo",
    "Ciepły narracyjny": "fable",
    "Mocny autorytatywny": "onyx",
    "Delikatny kobiecy": "nova",
    "Spokojny uspokajający": "shimmer"
}

AFFIRMATION_LENGTH_OPTIONS = ["1-2 zdania", "3-4 zdań", "5-6 zdań"]

# --------------------------
# Inicjalizacja stanu sesji
# --------------------------

def init_session_state():
    session_vars = {
        'editing': False,
        'edited_affirmation': "",
        'audio_data': None,
        'affirmation': "",
        'selected_voice': "fable",
        'api_key': "",
        'history': []
    }
    for key, value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --------------------------
# Funkcje pomocnicze
# --------------------------

def get_text_download_link(text, filename="afirmacja.txt"):
    b64 = base64.b64encode(text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="display:inline-block;padding:8px 20px;font-size:16px;font-weight:bold;color:white;background-color:#388E3C;text-align:center;border-radius:5px;text-decoration:none;">Pobierz TXT</a>'

def save_to_history(affirmation):
    if affirmation and affirmation not in st.session_state.history:
        st.session_state.history.append(affirmation)

# --------------------------
# Konfiguracja API
# --------------------------

st.set_page_config(page_title="Generator Afirmacji AI", page_icon="✨", layout="centered")

# env = dotenv_values(".env")
# api_key = env.get("OPENAI_API_KEY") or st.session_state.api_key
api_key = st.secrets["openai"]["OPENAI_API_KEY"]

if not api_key:
    st.warning("Brak klucza API w pliku .env! Wprowadź swój klucz poniżej:")
    api_key = st.text_input("Wpisz swój klucz API OpenAI:", type="password")
    if api_key:
        st.session_state.api_key = api_key
        st.rerun()

if not st.session_state.api_key:
    st.stop()

if "openai" not in st.secrets:
    st.error("Brak konfiguracji sekretów OpenAI!")
    st.stop()

client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

# --------------------------
# Interfejs użytkownika
# --------------------------

st.markdown("<h1 style='text-align: center;'>✨ AFIRMATOR ✨</h1>", unsafe_allow_html=True)
st.markdown("Wypełnij poniższe pola, a AI stworzy dla Ciebie unikalną afirmację!")

with st.form("afirmation_form", border=False):
    user_name = st.text_input("Twoje imię:")
    focus_area = st.selectbox("Nad czym chcesz popracować?", 
                            ["Pewność siebie", "Motywacja", "Wyciszenie", "Relacje", "Zdrowie", "Inne"])
    
    specific_goal = st.text_area("Wprowadź swój cel:")
    emotion_state = st.selectbox("Jak się obecnie czujesz w tej kwestii?", 
                               ["Neutralnie", "Zmęczony/a", "Zniechęcony/a", "Zestresowany/a", "Pełen/Pełna nadziei"])
    preferred_style = st.selectbox("Preferowany styl afirmacji:", 
                                 ["Łagodny", "Energiczny", "Poetycki", "Naukowy"])
    
    affirmation_length = st.selectbox("Jak długą afirmację preferujesz?", AFFIRMATION_LENGTH_OPTIONS)
    affirmation_timing = st.selectbox("Kiedy chcesz stosować afirmację?", 
                                    ["W ciągu dnia", "Rano", "Wieczorem"])
    affirmation_tone = st.selectbox("Jaki ton powinna mieć afirmacja?", 
                                  ["Spokojny", "Energiczny", "Podnoszący na duchu", "Mocny i stanowczy"])
    
    submitted = st.form_submit_button("Stwórz afirmację!")

# --------------------------
# Generowanie afirmacji
# --------------------------

if submitted:
    if not user_name:
        st.warning("Proszę wprowadzić swoje imię!")
        st.stop()

    target_focus = specific_goal if focus_area == "Inne" else focus_area
    
    prompt = f"""
    Stwórz spersonalizowaną afirmację dla {user_name} w języku polskim, która:
    1. Skoncentruje się na: {target_focus}
    2. Zaczyna się od \"Ja {user_name}\"
    3. Uwzględni obecny stan emocjonalny: {emotion_state}
    4. Odniesie się do konkretnego celu: {specific_goal}
    5. Będzie w stylu: {preferred_style}
    6. Użyje pozytywnego języka w czasie teraźniejszym
    7. Będzie miała długość: {affirmation_length}
    8. Powinna być stosowana: {affirmation_timing}
    9. Powinna mieć ton: {affirmation_tone}
    10. Zawiera elementy wizualizacji i emocji
    """
    
    try:
        with st.spinner("🧠 AI tworzy Twoją unikalną afirmację..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Jesteś doświadczonym coachem specjalizującym się w tworzeniu skutecznych afirmacji."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=250
            )
            
            affirmation = response.choices[0].message.content.strip('"')
            st.session_state.update({
                'affirmation': affirmation,
                'edited_affirmation': affirmation,
                'audio_data': None
            })
            save_to_history(affirmation)

    except Exception as e:
        st.error(f"Błąd podczas generowania afirmacji: {str(e)}")

# --------------------------
# Wyświetlanie i edycja
# --------------------------

if st.session_state.affirmation:
    st.markdown("---")
    st.success("### Twoja spersonalizowana afirmacja:")
    
    if st.session_state.editing:
        st.session_state.edited_affirmation = st.text_area(
            "Edytuj afirmację:",
            value=st.session_state.edited_affirmation,
            height=150
        )
        if st.button("Zapisz zmiany"):
            st.session_state.editing = False
            st.session_state.audio_data = None
            st.rerun()
    else:
        st.markdown(f"> *{st.session_state.edited_affirmation}*")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Edytuj"):
                st.session_state.editing = True
                st.rerun()
        with col2:
            st.markdown(get_text_download_link(st.session_state.edited_affirmation), unsafe_allow_html=True)
    
    st.markdown("---")

    # Generowanie audio
    col1, col2 = st.columns(2)
    with col1:
        voice_label = st.radio(
            "Wybierz głos:",
            options=list(VOICE_OPTIONS.keys()),
            index=2,
            help="Wybierz preferowany styl głosu dla generowanej wypowiedzi"
        )
        st.session_state.selected_voice = VOICE_OPTIONS[voice_label]

        if st.button("Przeczytaj afirmację 🎧"):
            try:
                with st.spinner("🔊 Generowanie audio..."):
                    audio_response = client.audio.speech.create(
                        model="tts-1",
                        voice=st.session_state.selected_voice,
                        input=st.session_state.edited_affirmation,
                        response_format="mp3"
                    )
                    st.session_state.audio_data = audio_response.content
            except Exception as e:
                st.error(f"Błąd generowania audio: {str(e)}")

    # Odtwarzanie i pobieranie
    if st.session_state.audio_data:
        with col2:
            st.audio(st.session_state.audio_data, format="audio/mp3")
            b64 = base64.b64encode(st.session_state.audio_data).decode()
            href = f'<a href="data:file/mp3;base64,{b64}" download="afirmacja.mp3" style="display:inline-block;padding:8px 20px;font-size:16px;font-weight:bold;color:white;background-color:#388E3C;text-align:center;border-radius:5px;text-decoration:none;">Pobierz MP3</a>'
            st.markdown(href, unsafe_allow_html=True)

    st.caption("💡 Porada: Powtarzaj tę afirmację przez 21 dni dla najlepszych efektów!")

# --------------------------
# Panel boczny z historią
# --------------------------

st.sidebar.markdown("### Historia afirmacji")
if st.session_state.history:
    selected = st.sidebar.selectbox("Wybierz wcześniejszą afirmację:", st.session_state.history)
    st.sidebar.markdown(f"**Wybrana afirmacja:**\n> {selected}")
else:
    st.sidebar.write("Brak zapisanych afirmacji.")
