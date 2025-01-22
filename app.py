import streamlit as st
import requests
import json
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, ForeignKey, MetaData, Row
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from streamlit_navigation_bar import st_navbar
import os
import time
from mem0 import Memory
from sqlalchemy import Boolean
import time



st.set_page_config(
    page_title="chat vllm and ollama",
    page_icon=":art:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Добавление CSS для оформления
st.markdown("""
    <style>
        :root {
            --retro-dark: #2A2D34;
            --retro-beige: #E8DAB2;
            --retro-muted-green: #76949F;
            --retro-muted-orange: #C8553D;
            --retro-border: #4A4E58;
        }

        /* Базовые стили */
        body {
            background: var(--retro-dark) !important;
            color: var(--retro-beige) !important;
            font-family: 'Courier New', monospace !important;
        }

        /* Основной контейнер */
        .stApp {
            max-width: 100vw !important;
            overflow-x: hidden !important;
        }

        /* Контейнер чата */
        .stChatMessageContainer {
            padding: 20px 5% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Сообщения */
        .user-message, .bot-response {
            max-width: 80% !important;
            margin: 15px 0 !important;
            padding: 20px !important;
            border-radius: 8px !important;
            word-wrap: break-word !important;
            position: relative;
            box-shadow: 4px 4px 0 var(--retro-border) !important;
        }

        .user-message {
            background: var(--retro-muted-orange) !important;
            margin-left: auto !important;
            border: 2px solid var(--retro-border) !important;
        }

        .bot-response {
            background: var(--retro-muted-green) !important;
            margin-right: auto !important;
            border: 2px solid var(--retro-border) !important;
        }

        /* Поле ввода */
        .stChatInput {
            padding: 0 5% 20px !important;
            max-width: 100% !important;
        }

        .stChatInput .stTextInput textarea {
            background: var(--retro-dark) !important;
            border: 2px solid var(--retro-border) !important;
            color: var(--retro-beige) !important;
            border-radius: 4px !important;
            padding: 15px !important;
            font-size: 16px !important;
        }

        /* Кнопка отправки */
        .stChatInput button {
            background: var(--retro-muted-green) !important;
            color: var(--retro-dark) !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 10px 25px !important;
            margin-top: 10px !important;
        }

        /* Вкладки */
        .stTabs [role="tablist"] {
            border-bottom: 2px solid var(--retro-border) !important;
            padding: 0 5% !important;
        }

        [data-baseweb="tab"] {
            color: var(--retro-beige) !important;
            padding: 12px 20px !important;
            margin: 0 5px !important;
        }

        [aria-selected="true"] {
            background: var(--retro-muted-orange) !important;
            color: var(--retro-dark) !important;
            border-radius: 4px 4px 0 0 !important;
        }

        /* Адаптивность */
        @media (max-width: 768px) {
            .user-message, .bot-response {
                max-width: 95% !important;
                margin: 15px 0 !important;
                padding: 15px !important;
            }

            .stTabs [role="tablist"] {
                padding: 0 2% !important;
            }

            [data-baseweb="tab"] {
                padding: 8px 12px !important;
                margin: 0 2px !important;
                font-size: 14px !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

hide_menu_style = """<style>#MainMenu {visibility: true;} footer {visibility: hidden;}</style>"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

custom_style = """
<style>
    #MainMenu {visibility: true;} /* Скрываем меню гамбургер */
    footer {visibility: true;}   /* Скрываем футер */
    .stDeployButton {
            display: none;
        }
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

def display_message(role, message):
    if role == "user":
        st.markdown(f'<div class="message-box user-message">{message}</div>', unsafe_allow_html=True)
    elif role == "bot":
        st.markdown(f'<div class="message-box bot-response">{message}</div>', unsafe_allow_html=True)

db_engine = create_engine("mysql+mysqlconnector://chat_user:1234@localhost/bot_app")
Session = sessionmaker(bind=db_engine)
session = Session()

metadata = MetaData()

# Описание таблиц
users_table = Table(
    'users', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('username', String(50), unique=True, nullable=False),
    Column('password', String(255), nullable=False)
)

messages_table = Table(
    'messages', metadata,
    Column('message_id', Integer, primary_key=True),
    Column('sender_id', Integer, ForeignKey('users.user_id'), nullable=False),
    Column('message_text', Text, nullable=False),
    Column('bot_response', Text, nullable=False),
    Column('chat_id', Integer, ForeignKey('chats.chat_id'), nullable=False)
)

chats_table = Table(
    'chats', metadata,
    Column('chat_id', Integer, primary_key=True),
    Column('creator_id', Integer, ForeignKey('users.user_id'), nullable=False),
    Column('chat_title', String(255), nullable=False),
    Column('created_at', Text, nullable=False, default=text("CURRENT_TIMESTAMP"))
)


metadata.create_all(db_engine)

def add_message(sender_id, message_text, bot_response, chat_id):
    try:
        query = text("""
            INSERT INTO messages (sender_id, message_text, bot_response, chat_id)
            VALUES (:sender_id, :message_text, :bot_response, :chat_id)
        """)
        with db_engine.connect() as conn:
            conn.execute(query, {
                'sender_id': sender_id,
                'message_text': message_text,
                'bot_response': bot_response,
                'chat_id': chat_id
            })
            conn.commit()
    except Exception as e:
        st.error(f"Error adding message: {e}")

def get_messages(chat_id):
    query = text("""
        SELECT message_text, bot_response
        FROM messages
        WHERE chat_id = :chat_id
        ORDER BY message_id ASC
    """)
    try:
        with db_engine.connect() as conn:
            result = conn.execute(query, {'chat_id': chat_id}).fetchall()
            return [{"user": row[0], "bot": row[1]} for row in result]
    except Exception as e:
        st.error(f"Error retrieving messages: {e}")
        return []

def login_user(username, password):
    with db_engine.connect() as conn:
        query = users_table.select().where(users_table.c.username == username)
        result = conn.execute(query).fetchone()
        if result and result.password == password:
            return result.user_id
    return None

def create_chat(creator_id):
    try:
        insert_chat_query = text("""
            INSERT INTO chats (chat_title, creator_id)
            VALUES (:chat_title, :creator_id)
        """)
        select_last_chat_query = text("""
            SELECT chat_id 
            FROM chats 
            WHERE creator_id = :creator_id 
            ORDER BY chat_id DESC 
            LIMIT 1
        """)

        with db_engine.begin() as conn:
            conn.execute(insert_chat_query, {"chat_title": "New Chat", "creator_id": creator_id})
            result = conn.execute(select_last_chat_query, {"creator_id": creator_id}).fetchone()
            if result and result[0]:
                return result[0]
            else:
                st.error("Error: Created chat ID not found")
                return None
    except Exception as e:
        st.error(f"Error creating chat: {e}")
        return None

def get_messages_for_chat(chat_id):
    query = text("""
        SELECT message_text, bot_response 
        FROM messages 
        WHERE chat_id = :chat_id
        ORDER BY message_id ASC
    """)
    try:
        with db_engine.connect() as conn:
            result = conn.execute(query, {'chat_id': chat_id}).fetchall()
            return [{'message_text': row[0], 'bot_response': row[1]} for row in result]
    except Exception as e:
        st.error(f"Ошибка при получении сообщений: {e}")
        return []


def update_chat_title(chat_id, chat_title):
    try:
        with db_engine.begin() as conn:
            update_query = text("""
                UPDATE chats
                SET chat_title = :chat_title
                WHERE chat_id = :chat_id
            """)
            conn.execute(update_query, {"chat_title": chat_title, "chat_id": chat_id})
    except Exception as e:
        st.error(f"Error updating chat title: {e}")

def verify_chat_update(chat_id):
    select_query = text(
        """
        SELECT id, chat_name FROM chats WHERE id = :chat_id
        """
    )
    with db_engine.connect() as conn:
        result = conn.execute(select_query, {"chat_id": chat_id}).fetchone()
        if result:
            st.write(f"Обновленное название чата с ID {chat_id}: {result[1]}")
        else:
            st.error(f"Ошибка: Чат с ID {chat_id} не найден после обновления.")
        
def get_chat(chat_id):
    try:
        select_query = text("SELECT * FROM chats WHERE chat_id = :chat_id")
        with db_engine.connect() as conn:
            result = conn.execute(select_query, {"chat_id": chat_id}).fetchone()
            return result
    except Exception as e:
        st.error(f"Error retrieving chat: {e}")
        return None

def get_user_chats(user_id):
    query = text("""
        SELECT chat_id, chat_title 
        FROM chats 
        WHERE creator_id = :creator_id 
        ORDER BY created_at DESC
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, {"creator_id": user_id}).fetchall()
        return [{"chat_id": row[0], "chat_title": row[1]} for row in result]

def search_messages(search_query, user_id=None):
    search_pattern = f"%{search_query}%"
    sql = text("""
        SELECT chat_id, message_text, bot_response
        FROM messages
        WHERE message_text LIKE :search_pattern OR bot_response LIKE :search_pattern
        """ + (" AND sender_id = :user_id" if user_id else ""))
    
    with db_engine.connect() as conn:
        params = {"search_pattern": search_pattern}
        if user_id:
            params["user_id"] = user_id
        result = conn.execute(sql, params).fetchall()
        return [{"chat_id": row[0], "message": row[1], "response": row[2]} for row in result]

def update_context_memory(chat_history, token_limit):
    context = ""
    for message in reversed(chat_history):
        context = f"User: {message['user']}\nBot: {message['bot']}\n" + context
        if len(context.split()) > token_limit:
            break
    return context.strip()

def stream_response(response_iterable, bot_container):
    response_text = ""
    for chunk in response_iterable:
        if chunk:
            try:
                chunk_data = json.loads(chunk)
                response_fragment = chunk_data.get("response", "")
                response_text += response_fragment

                bot_container.markdown(
                    f"<div style='background-color: #e8eaf6; padding: 10px; border-radius: 5px;'>{response_text}</div>",
                    unsafe_allow_html=True
                )
            except json.JSONDecodeError:
                st.error("Ошибка декодирования потока.")
    return response_text

def clean_response_text(raw_response):
    return re.sub(r'\s+', ' ', raw_response).strip() 

def extract_streaming_response(raw_response):
    json_pattern = r'\{.*?\}'  
    matches = re.findall(json_pattern, raw_response)

    response_text = []
    for match in matches:
        try:
            parsed = json.loads(match)
            response_text.append(parsed.get("response", "").strip())
        except json.JSONDecodeError:
            st.warning(f"Ошибка обработки JSON: {match}")
    return clean_response_text(" ".join(response_text))

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'page' not in st.session_state:
    st.session_state['page'] = "Авторизация"

if 'show_chats' not in st.session_state:
    st.session_state['show_chats'] = False
if 'max_chats' not in st.session_state:
    st.session_state['max_chats'] = 5
if 'model' not in st.session_state:
    st.session_state['model'] = "Qwen/Qwen2-beta-7B-Chat"
if 'platform' not in st.session_state:
    st.session_state['platform'] = "VLLM"
if 'selected_chat' not in st.session_state:
    st.session_state['selected_chat'] = None

if 'current_chat_id' not in st.session_state:
    st.session_state['current_chat_id'] = None
if 'is_new_chat' not in st.session_state:
    st.session_state['is_new_chat'] = True

def attempt_login():
    user_id = login_user(st.session_state.username, st.session_state.password)
    if user_id:
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = user_id
        st.session_state['page'] = "Новый чат"
        st.session_state['selected_chat'] = None 
        st.rerun()
    else:
        st.warning("Неверные данные")

if st.session_state['logged_in'] == False and st.session_state['page'] == "Авторизация":
    st.title("Авторизация")

    with st.form("login_form"):
        username = st.text_input("Логин", key="username", placeholder="Введите логин", label_visibility="collapsed")
        password = st.text_input("Пароль", type='password', key="password", placeholder="Введите пароль", label_visibility="collapsed")
        
        submit_button = st.form_submit_button("Войти")
    
    if submit_button:
        attempt_login()

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Chat"

if st.session_state['logged_in']:
    tab1, tab2, tab3 = st.tabs(["Новый чат", "Выбор модели", "Настройки"])

    if 'current_chat_id' not in st.session_state:
        st.session_state['current_chat_id'] = None
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'is_new_chat' not in st.session_state:
        st.session_state['is_new_chat'] = True

    with tab1:

        style_input = """
        <style>
            .stTextInput, .stChatInput {
                position: fixed;
                bottom: 0;
                center: 1;
                width: 50%;
                z-index: 1000;  
                padding: 10px;
                box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
            }
            .main {
                padding-bottom: 100px;  
            }
        </style>
        """
        st.markdown(style_input, unsafe_allow_html=True)

        st.title("Чат с моделью")

        for msg in st.session_state['chat_history']:
            display_message("user", msg['user'])
            display_message("bot", msg['bot'])
            st.write("---")

        if prompt := st.chat_input("Введите ваше сообщение:", key="new_chat_input"):
            # Проверка авторизации
            if 'user_id' not in st.session_state:
                st.error("Пользователь не авторизован. Пожалуйста, войдите в систему.")
                st.stop()

            user_id = st.session_state['user_id']
            chat_id = st.session_state.get('current_chat_id')

            if not chat_id:
                chat_id = create_chat(user_id)
                st.session_state['current_chat_id'] = chat_id
                st.session_state['is_new_chat'] = True

            if chat_id:
                response_text = ""
                bot_container = st.empty()

                if st.session_state['platform'] == "VLLM":
                    try:
                        display_message("user", prompt)
                        bot_container = st.empty()

                        chat_id = st.session_state.get("current_chat_id")
                        if not chat_id:
                            chat_id = create_chat(st.session_state["user_id"])
                            st.session_state["current_chat_id"] = chat_id

                        TOKEN_LIMIT = 1000
                        context = update_context_memory(st.session_state["chat_history"], TOKEN_LIMIT)

                        full_prompt = f"{context}\nUser: {prompt}\nBot:"

                        response = requests.post(
                            "http://localhost:8002/v1/completions",
                            headers={"Content-Type": "application/json"},
                            json={"prompt": full_prompt, "model": st.session_state.model}
                        )

                        if response.status_code == 200:
                            response_json = response.json()
                            response_text = response_json.get("choices", [{}])[0].get("text", "").strip()

                            if response_text:
                                display_message("bot", response_text)
                                st.session_state["chat_history"].append({"user": prompt, "bot": response_text})

                                chat_id = st.session_state.get("current_chat_id")
                                if not chat_id: 
                                    chat_id = create_chat(st.session_state["user_id"])
                                    if chat_id:
                                        st.session_state["current_chat_id"] = chat_id
                                    else:
                                        st.error("Ошибка: Не удалось создать новый чат.")
                                        st.stop()

                                last_response = response_text.strip()

                                if len(st.session_state["chat_history"]) == 1:
                                    chat_title_prompt = f"""
                                    Ты — модель для генерации названий чатов. Твоя задача — создать короткое и информативное название для чата на основе последнего сообщения, которое ты сама написала вот оно: {last_response}. Название должно быть кратким, четким, и легко воспринимаемым, чтобы оно отражало основной контекст разговора, без дополнительных знаков или лишних слов.
                                    Теперь, основываясь на последнем сообщении, создай подходящее название чата. 
                                    Пиши только название, больше ничего.                               
                                    """
                                    title_response = requests.post(
                                        "http://localhost:8002/v1/completions",
                                        headers={"Content-Type": "application/json"},
                                        json={
                                            "prompt": chat_title_prompt,
                                            "model": st.session_state.model,
                                            "max_tokens": 20,
                                            "temperature": 0.7,
                                        },
                                    )
                                    if title_response.status_code == 200:
                                        try:
                                            chat_title = title_response.json().get("choices", [{}])[0].get("text", "").strip() or "Новый чат"
                                            update_chat_title(chat_id, chat_title)
                                        except Exception as e:
                                            st.error(f"Ошибка обработки ответа: {e}")
                                    else:
                                        st.error(f"Ошибка модели при генерации названия чата: {title_response.status_code}")

                                add_message(st.session_state["user_id"], prompt, response_text, chat_id)

                            else:
                                st.error("Ответ от модели VLLM пустой.")
                        else:
                            st.error(f"Ошибка при запросе к VLLM. Код ошибки: {response.status_code}")
                    except Exception as e:
                        st.error(f"Ошибка при запросе к VLLM: {str(e)}")

                elif st.session_state['platform'] == "Ollama":
                    try:
                        display_message("user", prompt)
                        bot_container = st.empty()

                        chat_id = st.session_state.get("current_chat_id")
                        if not chat_id:
                            chat_id = create_chat(st.session_state["user_id"])
                            st.session_state["current_chat_id"] = chat_id

                        TOKEN_LIMIT = st.session_state.get("memory_token_limit", 1000)
                        context = update_context_memory(st.session_state["chat_history"], TOKEN_LIMIT)

                        system_instruction = "Ты – эксперт, отвечай подробно и обоснованно. Не допусти галлюцинаций."
                        full_prompt = f"{system_instruction}\n{context}\nUser: {prompt}\nBot:"

                        with bot_container:
                            st.markdown(
                                """
                                <div id="thinking-animation" style="display:flex; align-items:center; gap:10px; 
                                    background-color:#f5f5f5; padding:10px; border-radius:5px; font-family:Arial, sans-serif;">
                                    <div class="spinner" style="width:15px; height:15px; border:3px solid #ccc; 
                                        border-top:3px solid #007BFF; border-radius:50%; animation: spin 1s linear infinite;">
                                    </div>
                                    <span><b>Бот:</b> Обдумываю ответ...</span>
                                </div>
                                <style>
                                    @keyframes spin {
                                        from {transform: rotate(0deg);}
                                        to {transform: rotate(360deg);}
                                    }
                                </style>
                                """, unsafe_allow_html=True
                            )

                        complete_response = ""
                        temp_container = st.empty()

                        is_streaming = st.session_state.get("streaming_output", True)

                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            headers={"Content-Type": "application/json"},
                            json={
                                "prompt": full_prompt,
                                "model": st.session_state.model,
                                "stream": is_streaming,
                                "temperature": 0.7,
                                "max_tokens": 1000
                            },
                            stream=is_streaming
                        )

                        if response.status_code == 200:
                            # Убираем анимацию
                            with bot_container:
                                bot_container.empty()

                            if is_streaming:
                                for line in response.iter_lines(decode_unicode=True):
                                    if line:
                                        try:
                                            json_response = json.loads(line)
                                            chunk = json_response.get("response", "")
                                            
                                            complete_response += chunk

                                            with temp_container:
                                                st.markdown(
                                                    f"""
                                                    <div style='background-color:#f9f9f9; 
                                                        padding:10px; 
                                                        border-radius:5px; 
                                                        font-family:Arial, sans-serif; 
                                                        font-size:16px;'>
                                                        {complete_response.strip()}
                                                    </div>
                                                    """, unsafe_allow_html=True)

                                            if json_response.get("done", False):
                                                break

                                        except json.JSONDecodeError:
                                            continue
                            else:
                                json_response = response.json()
                                complete_response = json_response.get("response", "")
                                temp_container.markdown(
                                    f"""
                                    <div style='background-color:#f9f9f9; 
                                        padding:10px; 
                                        border-radius:5px; 
                                        font-family:Arial, sans-serif; 
                                        font-size:16px;'>
                                        {complete_response.strip()}
                                    </div>
                                    """, unsafe_allow_html=True
                                )

                            st.session_state["chat_history"].append({"user": prompt, "bot": complete_response})
#                            add_message(st.session_state["user_id"], prompt, complete_response, chat_id)

                            chat_id = st.session_state.get("current_chat_id")
                            if not chat_id:
                                chat_id = create_chat(st.session_state["user_id"])
                                if chat_id:
                                    st.session_state["current_chat_id"] = chat_id
                                else:
                                    st.error("Ошибка: Не удалось создать новый чат.")
                                    st.stop()

                            last_response = complete_response.strip()

                            if st.session_state.get('is_new_chat', True):
                                # Генерируем название чата
                                chat_title_prompt = f"""
                                    Ты — модель для генерации названий чатов. Твоя задача — создать короткое и информативное название для чата на основе последнего сообщения, которое ты сама написала вот оно: {complete_response}. Название должно быть кратким, четким, и легко воспринимаемым, чтобы оно отражало основной контекст разговора.
                                    Исключи все лишние слова и приветствия, пиши только название, 3 слова максимум, без вводных слов и названий.
                                """

                                with bot_container:
                                     st.markdown(
                                        """
                                        <div id="thinking-animation" style="display:flex; align-items:center; gap:10px; 
                                            background-color:#f5f5f5; padding:10px; border-radius:5px; font-family:Arial, sans-serif;">
                                            <div class="spinner" style="width:15px; height:15px; border:3px solid #ccc; 
                                                border-top:3px solid #007BFF; border-radius:50%; animation: spin 1s linear infinite;">
                                            </div>
                                            <span><b>Бот:</b> Обдумываю название чата...</span>
                                        </div>
                                        <style>
                                            @keyframes spin {
                                                from {transform: rotate(0deg);}
                                                to {transform: rotate(360deg);}
                                            }
                                        </style>
                                        """, unsafe_allow_html=True
                                    )

                                title_response = requests.post(
                                    "http://localhost:11434/api/generate",
                                    headers={"Content-Type": "application/json"},
                                    json={
                                        "prompt": chat_title_prompt,
                                        "model": st.session_state.model,
                                        "max_tokens": 20,
                                        "temperature": 0.7,
                                    },
                                    stream = is_streaming
                                )
                                full_response_text = ""
                                if title_response.status_code == 200:

                                    with bot_container:
                                        bot_container.empty()

                                    if is_streaming:
                                        for line in title_response.iter_lines(decode_unicode=True):
                                            if line:
                                                try:
                                                    response_part = json.loads(line)
                                                    if "response" in response_part:
                                                        full_response_text += response_part["response"]
                                                except json.JSONDecodeError:
                                                    continue
                                    else:
                                        full_response_text = title_response.json().get("response", "")

                                    try:
                                        chat_title = full_response_text.strip() or "Новый чат"
                                        chat_title_words = chat_title.split()
                                        if len(chat_title_words) > 3:
                                            chat_title = " ".join(chat_title_words[:3])  # Ограничение до 3 слов

                                        update_chat_title(chat_id, chat_title)  # Обновление названия чата
                                        st.session_state['is_new_chat'] = False  # Устанавливаем флаг, чтобы не повторять генерацию
                                    except Exception as e:
                                        st.error(f"Ошибка обработки ответа: {e}")
                                else:
                                    st.error(f"Ошибка модели при генерации названия чата: {title_response.status_code}")
                            add_message(st.session_state["user_id"], prompt, complete_response, chat_id)

                        else:
                            st.error(f"Ошибка модели: {response.status_code} - {response.text}")

                    except requests.exceptions.RequestException as e:
                        st.error(f"Ошибка подключения: {e}")


    with tab2:
        st.session_state['platform'] = st.selectbox("Выберите платформу", ["VLLM", "Ollama"], index=["VLLM", "Ollama"].index(st.session_state['platform']), key="select")

        if st.session_state['platform'] == "VLLM":
            st.session_state['model'] = st.selectbox("Выберите модель", ["Qwen/Qwen2-beta-7B-Chat", "MTSAIR/Cotype-Nano", "Model3"], index=0)
        elif st.session_state['platform'] == "Ollama":
            st.session_state['model'] = st.selectbox("Выберите модель", ["llama3.2", "qwen2.5-coder", "llama3.2:1b"], index=0)
    
    with tab3:
        st.title("Настройки")

        show_chats = st.checkbox("Показывать другие чаты", value=st.session_state.get('show_chats', False))
        if show_chats != st.session_state.get('show_chats', False):
            st.session_state['show_chats'] = show_chats

        max_chats = st.number_input(
            "Сколько чатов показывать?",
            min_value=1,
            max_value=40,
            value=st.session_state.get('max_chats', 10),  # Значение по умолчанию 10
            step=1,
            format="%d"
        )
        if max_chats != st.session_state['max_chats']:
            st.session_state['max_chats'] = max_chats
            st.rerun()

        memory_token_limit = st.number_input(
            "Количество токенов для памяти", 
            min_value=100, 
            value=1000, 
            step=100, 
            help="Максимальное количество токенов, используемых для контекста памяти."
        )
        st.session_state['memory_token_limit'] = memory_token_limit

        streaming_output = st.checkbox(
            "Потоковый вывод ответа модели", 
            value=True, 
            help="Включите, чтобы получать ответ модели по мере генерации."
        )
        st.session_state['streaming_output'] = streaming_output
    
def switch_tab(tab_name):
    st.session_state.active_tab = tab_name

def switch_page(page):
    st.session_state.page = page
    st.rerun()

style_side = """
<style>
.sidebar-button {
    background-color: #FF6347;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 10px 0;
    cursor: pointer;
    width: 100%;
}

.sidebar-button:hover {
    background-color: #FF4500;
}
</style>
"""

st.markdown(style_side, unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True

def logout():
    st.session_state.clear()
    st.rerun()

button_style = """
<style>
.stButton > button {
    background-color: #E0E5EC;
    color: #4A4A4A;        
    border: none;           
    border-radius: 12px;      
    padding: 10px 20px;      
    font-size: 16px;         
    font-weight: bold;         
    box-shadow: 2px 2px 5px #BEC4CC, -2px -2px 5px white; 
    cursor: pointer;      
    margin: 10px 0;            
    transition: all 0.2s ease; 
}

.stButton > button:hover {
    background-color: #D6DBE0; 
    box-shadow: inset 2px 2px 5px #BEC4CC, inset -2px -2px 5px white; 
    color: #2F2F2F;            
}
</style>
"""

st.markdown(button_style, unsafe_allow_html=True)

if st.session_state['logged_in']:
    with st.sidebar:

        st.markdown(
            f"""
            <div style='display: flex; align-items: center;'>
                <h1 style='margin: 0;'>Панель управления</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        search_query = st.text_area(
            "Введите текст для поиска:",
            placeholder="Введите текст...",
            key="search_query",
            height=70,
        )

        if search_query.strip():
            user_id = st.session_state.get("user_id")
            search_results = search_messages(search_query.strip(), user_id)

            if 'show_results' not in st.session_state:
                st.session_state['show_results'] = True
        
            with st.sidebar:
                if st.session_state['show_results']:
                    if st.button("Скрыть"):
                        st.session_state['show_results'] = False
                        st.rerun()
                else:
                    if st.button("Показать"):
                        st.session_state['show_results'] = True
                        st.rerun()

            if st.session_state['show_results']:
                if search_results:
                    st.subheader("Результаты поиска:")
                    for result in search_results:
                        st.write(f"**Чат ID:** {result['chat_id']}")
                        st.write(f"**Сообщение:** {result['message']}")
                        st.write(f"**Ответ:** {result['response']}")
                        st.write("---")
                else:
                    st.write("Результаты не найдены.")
    
        else:
            st.warning("Введите текст для поиска.")

        if st.session_state['show_chats']:
            st.subheader("Ваши чаты")
            user_id = st.session_state['user_id']
            chats = get_user_chats(user_id)

            for chat in chats[:st.session_state['max_chats']]:
                chat_id = chat["chat_id"]
                chat_name = chat["chat_title"] if chat["chat_title"] else f"Чат {chat_id}"

                if st.session_state.get('selected_chat') == chat_id:
                    if st.button(f"Выйти из чата: {chat_name}", key=f"exit_chat_{chat_id}"):
                        st.session_state['selected_chat'] = None
                        st.session_state['page'] = "Новый чат"
                        st.rerun()
                else:
                    if st.button(chat_name, key=f"chat_{chat_id}"):
                        st.session_state['selected_chat'] = chat_id
                        st.session_state['page'] = "Чаты"
                        st.session_state['current_chat_id'] = chat_id
                        st.rerun()

        if st.button("Выйти", key="logout_button"):
            st.session_state.clear()
            st.rerun()


if st.session_state['logged_in'] and st.session_state['page'] == "Настройки":
    st.title("Настройки")
    st.session_state['show_chats'] = st.checkbox("Показывать другие чаты", value=st.session_state['show_chats'])

    st.session_state['max_chats'] = st.number_input(
        "Сколько чатов показывать?",
        min_value=1,
        max_value=100,
        value=st.session_state['max_chats'],
        step=1,
        format="%d"
    )

    if st.button("Выйти из настроек"):
        st.session_state['page'] = "Чаты" if 'selected_chat' in st.session_state else "Новый чат"
        st.rerun()

    st.markdown(
        """
        <style>
            .css-1kyxreq {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

if st.session_state['logged_in'] and st.session_state['page'] == "Чаты":
    st.title(f"Чат {st.session_state['selected_chat']}")

    messages = get_messages_for_chat(st.session_state['selected_chat'])

    for message in messages:
        if message['message_text']:
            display_message("user", message['message_text'])
        
        if message['bot_response']:
            display_message("bot", message['bot_response'])

    prompt = st.chat_input("Введите ваше сообщение:", key=f"chat_input_{st.session_state['selected_chat']}")
    if prompt:
        user_id = st.session_state['user_id']
        chat_id = st.session_state['selected_chat']

        response_text = ""

        if st.session_state['platform'] == "VLLM":
            try:
                response = requests.post(
                    "http://localhost:8002/v1/completions",
                    headers={"Content-Type": "application/json"},
                    json={"prompt": prompt, "model": st.session_state.model}
                )

                if response.status_code == 200:
                    response_json = response.json()
                    response_text = response_json.get("choices", [{}])[0].get("text", "").strip()

                    if response_text:
                        display_message("user", prompt)
                        display_message("bot", response_text)
                    else:
                        st.error("Ответ от модели VLLM пустой.")
                else:
                    st.error(f"Ошибка при запросе к VLLM. Код ошибки: {response.status_code}")
            except Exception as e:
                st.error(f"Ошибка при запросе к VLLM: {str(e)}")

        elif st.session_state['platform'] == "Ollama":
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    headers={"Content-Type": "application/json"},
                    json={"model": "llama3.2", "prompt": prompt}
                )

                if response.status_code == 200:
                    response_lines = response.text.strip().split('\n')
                    full_output = ""
                    for line in response_lines:
                        try:
                            line = line.strip().strip('{}')
                            response_json = json.loads('{' + line + '}')
                            full_output += response_json.get("response", "")
                        except json.JSONDecodeError:
                            continue

                    response_text = full_output.strip()

                    if response_text:
                        # Отображение сообщений в интерфейсе
                        display_message("user", prompt)
                        display_message("bot", response_text)
                    else:
                        st.error("Ответ от модели Ollama пустой.")
                else:
                    st.error(f"Ошибка при запросе к Ollama. Код ошибки: {response.status_code}")
            except Exception as e:
                st.error(f"Ошибка при запросе к Ollama: {str(e)}")

        if response_text:
            add_message(user_id=user_id, message=prompt, response=response_text, chat_id=chat_id)
        else:
            st.error("Не удалось получить ответ от модели.")
