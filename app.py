import streamlit as st
import requests

# 1. הגדרות עיצוב מתקדמות
st.set_page_config(page_title="החבר הדיגיטלי", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #1a1a1a !important; color: #ffffff !important; }
    div.block-container { background-color: #1a1a1a !important; }
    [data-testid="stChatMessage"] { background-color: #2d2d2d !important; border-radius: 12px !important; padding: 15px !important; }
    [data-testid="stChatInput"] { background-color: #1a1a1a !important; }
    [data-testid="stChatInput"] > div > div > input {
        background-color: #2d2d2d !important; color: white !important;
        border: 1px solid #444 !important; border-radius: 20px !important;
    }
    h1 { color: #f0f0f0 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. ממשק המשתמש
with st.sidebar:
    st.title("⚙️ הגדרות")
    system_instruction = st.text_area("תפקיד הבוט:", "אתה עוזר חכם, נחמד ומקצועי.")
    if st.button("נקה צ'אט 🔄"):
        st.session_state.messages = []
        st.rerun()

st.title("🤖 החבר הדיגיטלי")

if "messages" not in st.session_state:
    st.session_state.messages = []

# הצגת השיחה
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 3. לוגיקת הצ'אט
if prompt := st.chat_input("כתבי משהו..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    api_key = st.secrets["GEMINI_API_KEY"]
    model_name = "gemini-2.0-flash" # מומלץ להשתמש בגרסה זו
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    with st.status("הבוט חושב...", expanded=True) as status:
        history = [{"role": "user", "parts": [{"text": f"תפקידך: {system_instruction}"}]}]
        for m in st.session_state.messages:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [{"text": m["content"]}]})
        
        try:
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": history}, timeout=30)
            
            # בדיקת חריגה מהמכסה (429)
            if response.status_code == 429:
                status.update(label="המכסה היומית נוצלה", state="error")
                st.warning("הגעת למגבלת השימוש החינמית להיום. המכסה תתאפס מחר.")
            
            elif response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    st.chat_message("assistant").markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    status.update(label="הבוט מוכן!", state="complete", expanded=False)
                else:
                    status.update(label="שגיאת מבנה", state="error")
                    st.error("התקבלה תשובה לא ברורה מהשרת.")
            else:
                status.update(label="שגיאת שרת", state="error")
                st.error(f"שגיאה: {response.status_code}")
                
        except Exception as e:
            st.error(f"לא ניתן להתחבר לבוט: {e}")
            status.update(label="קרתה שגיאה", state="error")
            