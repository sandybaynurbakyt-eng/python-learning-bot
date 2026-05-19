import os
from dotenv import load_dotenv
import telebot
from telebot import types
from groq import Groq
import sqlite3

load_dotenv()

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("Ошибка: Переменная 'TOKEN' не найдена. Проверьте файл .env")
if not GROQ_API_KEY:
    raise ValueError("Ошибка: Переменная 'GROQ_API_KEY' не найдена. Проверьте файл .env")

bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_API_KEY)

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
               CREATE TABLE IF NOT EXISTS users
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY,
                   xp
                   INTEGER,
                   progress
                   INTEGER
               )
               """)
conn.commit()

question_step = {}

lessons = [
    {
        "topic": "Variables",
        "lecture": "📘 Переменные\n\nПеременная — это имя для хранения значения.\n\nПример:\nx = 5\nname = \"Alex\"\n\nПеременные можно менять:\nx = 5\nx = 10\n\nТипы:\nint, string, bool",
        "questions": [
            {"q": "Что такое переменная?", "options": ["Имя для хранения значения", "Функция", "Цикл"],
             "answer": "Имя для хранения значения"},
            {"q": "Что делает x = 5?", "options": ["Создает переменную", "Удаляет", "Цикл"],
             "answer": "Создает переменную"},
            {"q": "Можно ли изменить значение?", "options": ["Да", "Нет", "Нет никогда"], "answer": "Да"}
        ]
    },
    {
        "topic": "Print",
        "lecture": "📘 print()\n\nprint выводит текст на экран.\n\nПример:\nprint(\"Hello\")\nprint(name)",
        "questions": [
            {"q": "Что делает print?", "options": ["Выводит текст", "Удаляет", "Создает"], "answer": "Выводит текст"},
            {"q": "print('Hi') → ?", "options": ["Hi", "Ошибка", "Ничего"], "answer": "Hi"},
            {"q": "Можно вывести переменную?", "options": ["Да", "Нет", "Только числа"], "answer": "Да"}
        ]
    },
    {
        "topic": "If",
        "lecture": "📘 Условия\n\nif проверяет условие.\n\nПример:\nif x > 5:\n    print(\"OK\")",
        "questions": [
            {"q": "Что делает if?", "options": ["Проверяет условие", "Цикл", "Функция"], "answer": "Проверяет условие"},
            {"q": "> это?", "options": ["Больше", "Меньше", "Равно"], "answer": "Больше"},
            {"q": "Когда выполняется код?", "options": ["Когда True", "Когда False", "Никогда"], "answer": "Когда True"}
        ]
    }
]


def level(points):
    if points < 50:
        return "Beginner 🐣"
    elif points < 150:
        return "Junior 🧑‍💻"
    else:
        return "Python Master 🚀"


def menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📚 Урок", "📊 Прогресс")
    markup.add("🏆 XP", "🤖 AI")
    markup.add("ℹ Помощь", "📖 Все темы")
    return markup


def get_user_data(user_id):
    cursor.execute("SELECT xp, progress FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        return {"xp": row[0], "progress": row[1]}
    return None


@bot.message_handler(commands=['start'])
def start(message):
    user = message.chat.id
    question_step[user] = 0

    cursor.execute(
        "INSERT OR IGNORE INTO users(id, xp, progress) VALUES(?, ?, ?)",
        (user, 0, 0)
    )
    conn.commit()

    bot.send_message(
        user,
        "👋 Добро пожаловать!\nУчись Python вместе со мной 🚀",
        reply_markup=menu()
    )


def send_lesson(user):
    data = get_user_data(user)
    step = data["progress"]

    if step >= len(lessons):
        bot.send_message(user, "🎉 Все уроки пройдены!")
        return

    lesson = lessons[step]
    text = f"📖 Урок {step + 1}: {lesson['topic']}\n{lesson['lecture']}"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("▶ Тест", "📋 Меню")

    bot.send_message(user, text, reply_markup=markup)


def send_question(user):
    data = get_user_data(user)
    step = data["progress"]
    q = question_step.get(user, 0)

    if step >= len(lessons):
        bot.send_message(user, "🎉 Вы уже прошли все уроки!")
        return

    question = lessons[step]["questions"][q]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for opt in question["options"]:
        markup.add(opt)
    markup.add("📋 Меню")

    bot.send_message(user, f"❓ {question['q']}", reply_markup=markup)


def ask_ai(question):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Ты учитель Python. Объясняй просто."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка AI: {e}"


@bot.message_handler(content_types=['text'])
def handle(message):
    user = message.chat.id
    text = message.text

    if not text.strip():
        bot.send_message(user, "❌ Пустое сообщение")
        return

    data = get_user_data(user)
    if not data:
        cursor.execute("INSERT INTO users(id, xp, progress) VALUES(?, 0, 0)", (user,))
        conn.commit()
        data = {"xp": 0, "progress": 0}

    if user not in question_step:
        question_step[user] = 0

    if text == "📚 Урок":
        send_lesson(user)

    elif text == "▶ Тест":
        question_step[user] = 0
        send_question(user)

    elif text == "📊 Прогресс":
        step = data["progress"]
        percent = int(step / len(lessons) * 100)
        bot.send_message(user, f"📊 {percent}% курса пройдено")

    elif text == "🏆 XP":
        current_xp = data["xp"]
        bot.send_message(user, f"🏆 XP: {current_xp}\n\n🎯 Уровень:\n{level(current_xp)}")

    elif text == "ℹ Помощь":
        bot.send_message(user,
                         "📚 Урок — открыть урок\n▶ Тест — пройти тест\n📊 Прогресс — посмотреть прогресс\n🏆 XP — посмотреть XP\n🤖 AI — задать вопрос AI\n📖 Все темы — список уроков")

    elif text == "📖 Все темы":
        topics = ""
        for i, lesson in enumerate(lessons):
            topics += f"{i + 1}. {lesson['topic']}\n"
        bot.send_message(user, f"📚 Темы курса:\n\n{topics}")

    elif text == "🤖 AI":
        bot.send_message(user, "Напиши вопрос в формате:\n/ask Ваш вопрос")

    elif text.startswith("/ask"):
        q = text.replace("/ask", "").strip()
        if q == "":
            bot.send_message(user, "❌ Напиши вопрос после /ask")
            return
        bot.send_message(user, "🤖 Думаю...")
        answer = ask_ai(q)
        bot.send_message(user, answer)

    elif text == "📋 Меню":
        question_step[user] = 0
        bot.send_message(user, "📋 Главное меню", reply_markup=menu())

    else:
        step = data["progress"]

        if step < len(lessons):
            q = question_step[user]
            current_lesson = lessons[step]

            if text not in current_lesson["questions"][q]["options"]:
                bot.send_message(user, "❓ Неизвестная команда. Выберите ответ на кнопках или вернитесь в 📋 Меню.")
                return

            question = current_lesson["questions"][q]

            if text == question["answer"]:
                question_step[user] += 1

                if question_step[user] == len(current_lesson["questions"]):
                    new_progress = step + 1
                    new_xp = data["xp"] + 20

                    cursor.execute(
                        "UPDATE users SET xp = ?, progress = ? WHERE id = ?",
                        (new_xp, new_progress, user)
                    )
                    conn.commit()

                    bot.send_message(user, "🎉 Урок пройден! +20 XP", reply_markup=menu())
                else:
                    send_question(user)
            else:
                bot.send_message(user, "❌ Неправильно! Попробуйте еще раз.")
        else:
            bot.send_message(user, "🎉 Курс полностью завершен!", reply_markup=menu())


print("Bot started...")
bot.polling(none_stop=True)
