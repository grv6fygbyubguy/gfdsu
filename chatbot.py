import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import sqlite3
import requests
from bs4 import BeautifulSoup
import googlesearch

# 🔑 Configure Gemini AI
genai.configure(api_key="AIzaSyAo1KQiL-hOO1MfIKrdZmNgTZ6a6gWcNU4")
model = genai.GenerativeModel("gemini-1.5-flash")

# 💾 SQLite Database
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS chat (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, message TEXT)")
conn.commit()

# 🎙️ Text-to-Speech
engine = pyttsx3.init()
engine.setProperty("rate", 150)

# 🛑 Memory for Context
chat_memory = []
last_mentioned_name = None  # Stores last entity/person mentioned

# 🌍 Google Search (Short Answer)
def search_google(query):
    """Search Google and return a short answer."""
    try:
        search_results = list(googlesearch.search(query, num_results=1))
        if search_results:
            url = search_results[0]
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")

            for p in soup.find_all("p"):
                if len(p.text) > 50:
                    return p.text.strip().split(".")[0] + "."
        return None
    except:
        return None

# 🧠 Chatbot Response (Short Answers + Context)
def chatbot_response(user_input):
    global last_mentioned_name  

    save_to_db("User", user_input)

    # 🔍 Google Search First
    google_result = search_google(user_input)
    if google_result:
        bot_reply = f"🔍 {google_result}"
    else:
        try:
            # If user asks "Who is he?", use last_mentioned_name
            if user_input.lower() in ["who is he", "who is she", "who is that"]:
                if last_mentioned_name:
                    user_input = f"Who is {last_mentioned_name}?"

            # 🧠 Short AI Response with Memory
            context = "\n".join(chat_memory[-5:])
            prompt = f"Previous conversation:\n{context}\nUser: {user_input}\nBot: (Give a short answer in 1-2 sentences)"

            response = model.generate_content(prompt)
            bot_reply = response.text.strip()

            # Update last mentioned name if chatbot identifies a person
            if "is" in user_input and len(user_input.split()) > 2:
                last_mentioned_name = user_input.split("is")[-1].strip().capitalize()

        except:
            bot_reply = "I don't know."

    chat_memory.append(f"User: {user_input}")
    chat_memory.append(f"Bot: {bot_reply}")

    save_to_db("Bot", bot_reply)
    return bot_reply

# 💾 Save Chat History
def save_to_db(role, message):
    cursor.execute("INSERT INTO chat (role, message) VALUES (?, ?)", (role, message))
    conn.commit()

# 🎙️ Voice Input
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            user_input = recognizer.recognize_google(audio)
            print(f"You: {user_input}")
            return user_input
        except:
            print("❌ Could not understand.")
            return None

# 🔊 Voice Output
def speak(text):
    engine.say(text)
    engine.runAndWait()
