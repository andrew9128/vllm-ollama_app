# vllm-ollama_app

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39.0-FF4B4B.svg)](https://streamlit.io/)

Интеллектуальный чат-интерфейс с поддержкой различных языковых моделей (LLM) и интеграцией с VLLM/Ollama серверами.

<img width="1439" alt="Screenshot 2025-01-22 at 8 40 27 PM" src="https://github.com/user-attachments/assets/e220b8db-599f-458d-a5eb-815864dfe256" />


## ✨ Особенности

- Поддержка нескольких LLM моделей (Qwen, Llama, и др.)
- Интеграция с VLLM и Ollama серверами
- История чатов с сохранением в MySQL
- Поиск по истории сообщений
- Настройка параметров генерации

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-username/ваш-репозиторий.git
cd ваш-репозиторий
```
2. Настройте базу данных:
```bash
CREATE DATABASE bot_app;
CREATE USER 'chat_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON chat_app.* TO 'chat_user'@'localhost';
```
3. Запуск:
```bash
streamlit run nia_for_pres.py
```
4. Запуск Ollama:
```bash
docker run -d -p 11434:11434 ollama/ollama
ollama pull llama2
ollama serve
```
5. Запуск VLLM:
```bash
docker run -d -p 8002:8002 vllm/vllm-openai --model Qwen/Qwen2-beta-7B-Chat
```
