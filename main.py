import telebot
from telebot import types
from groq import Groq
import sqlite3

# =========================
# TOKENS
# =========================

TOKEN = "ТОКЕН БОТ"
GROQ_API_KEY = "Токен ии"



bot = telebot.TeleBot(TOKEN)
client = Groq(api_key=GROQ_API_KEY)



conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    xp INTEGER,
    progress INTEGER
)
""")

conn.commit()



progress = {}
xp = {}
question_step = {}



lessons = [
    {
        "topic": "Variables",
        "lecture": """
📘 Переменные

Переменная — это имя для хранения значения.

Пример:
x = 5
name = "Alex"

Переменные можно менять:
x = 5
x = 10

Типы:
int, string, bool
""",
        "questions": [
            {
                "q": "Что такое переменная?",
                "options": [
                    "Имя для хранения значения",
                    "Функция",
                    "Цикл"
                ],
                "answer": "Имя для хранения значения"
            },
            {
                "q": "Что делает x = 5?",
                "options": [
                    "Создает переменную",
                    "Удаляет",
                    "Цикл"
                ],
                "answer": "Создает переменную"
            },
            {
                "q": "Можно ли изменить значение?",
                "options": [
                    "Да",
                    "Нет",
                    "Нет никогда"
                ],
                "answer": "Да"
            }
        ]
    },

    {
        "topic": "Print",
        "lecture": """
📘 print()

print выводит текст на экран.

Пример:
print("Hello")
print(name)
""",
        "questions": [
            {
                "q": "Что делает print?",
                "options": [
                    "Выводит текст",
                    "Удаляет",
                    "Создает"
                ],
                "answer": "Выводит текст"
            },
            {
                "q": "print('Hi') → ?",
                "options": [
                    "Hi",
                    "Ошибка",
                    "Ничего"
                ],
                "answer": "Hi"
            },
            {
                "q": "Можно вывести переменную?",
                "options": [
                    "Да",
                    "Нет",
                    "Только числа"
                ],
                "answer": "Да"
            }
        ]
    },

    {
        "topic": "If",
        "lecture": """
📘 Условия

if проверяет условие.

Пример:
if x > 5:
    print("OK")
""",
        "questions": [
            {
                "q": "Что делает if?",
                "options": [
                    "Проверяет условие",
                    "Цикл",
                    "Функция"
                ],
                "answer": "Проверяет условие"
            },
            {
                "q": "> это?",
                "options": [
                    "Больше",
                    "Меньше",
                    "Равно"
                ],
                "answer": "Больше"
            },
            {
                "q": "Когда выполняется код?",
                "options": [
                    "Когда True",
                    "Когда False",
                    "Никогда"
                ],
                "answer": "Когда True"
            }
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



@bot.message_handler(commands=['start'])
def start(message):

    user = message.chat.id

    progress[user] = 0
    xp[user] = 0
    question_step[user] = 0

    cursor.execute(
        "INSERT OR IGNORE INTO users(id,xp,progress) VALUES(?,?,?)",
        (user, 0, 0)
    )

    conn.commit()

    bot.send_message(
        user,
        "👋 Добро пожаловать!\n\nУчись Python 🚀",
        reply_markup=menu()
    )



def send_lesson(user):

    step = progress[user]

    if step >= len(lessons):
        bot.send_message(
            user,
            "🎉 Все уроки пройдены!"
        )
        return

    lesson = lessons[step]

    text = f"""
📖 Урок {step + 1}: {lesson['topic']}

{lesson['lecture']}
"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("▶ Тест", "📋 Меню")

    bot.send_message(
        user,
        text,
        reply_markup=markup
    )



def send_question(user):

    step = progress[user]
    q = question_step[user]

    question = lessons[step]["questions"][q]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for opt in question["options"]:
        markup.add(opt)

    bot.send_message(
        user,
        f"❓ {question['q']}",
        reply_markup=markup
    )



def ask_ai(question):

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Ты учитель Python. Объясняй просто."
                },
                {
                    "role": "user",
                    "content": question
                }
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
        bot.send_message(
            user,
            "❌ Пустое сообщение"
        )
        return



    if user not in progress:

        progress[user] = 0
        xp[user] = 0
        question_step[user] = 0



    if text == "📚 Урок":
        send_lesson(user)



    elif text == "▶ Тест":

        question_step[user] = 0
        send_question(user)



    elif text == "📊 Прогресс":

        step = progress[user]

        percent = int(
            step / len(lessons) * 100
        )

        bot.send_message(
            user,
            f"📊 {percent}% курса"
        )



    elif text == "🏆 XP":

        bot.send_message(
            user,
            f"""
🏆 XP: {xp[user]}

🎯 Уровень:
{level(xp[user])}
"""
        )



    elif text == "ℹ Помощь":

        bot.send_message(
            user,
            """
📚 Урок — открыть урок

▶ Тест — пройти тест

📊 Прогресс — посмотреть прогресс

🏆 XP — посмотреть XP

🤖 AI — задать вопрос AI

📖 Все темы — список уроков
"""
        )



    elif text == "📖 Все темы":

        topics = ""

        for i, lesson in enumerate(lessons):
            topics += f"{i + 1}. {lesson['topic']}\n"

        bot.send_message(
            user,
            f"📚 Темы курса:\n\n{topics}"
        )



    elif text == "🤖 AI":

        bot.send_message(
            user,
            "Напиши:\n/ask вопрос"
        )



    elif text.startswith("/ask"):

        q = text.replace("/ask", "")

        if q.strip() == "":

            bot.send_message(
                user,
                "❌ Напиши вопрос после /ask"
            )

            return

        bot.send_message(
            user,
            "🤖 Думаю..."
        )

        answer = ask_ai(q)

        bot.send_message(
            user,
            answer
        )



    elif text == "📋 Меню":

        bot.send_message(
            user,
            "📋 Главное меню",
            reply_markup=menu()
        )



    else:

        step = progress[user]

        if step < len(lessons):

            q = question_step[user]

            question = lessons[step]["questions"][q]

            if text == question["answer"]:

                question_step[user] += 1

                if question_step[user] == len(lessons[step]["questions"]):

                    progress[user] += 1
                    xp[user] += 20

                    cursor.execute(
                        """
                        UPDATE users
                        SET xp=?, progress=?
                        WHERE id=?
                        """,
                        (
                            xp[user],
                            progress[user],
                            user
                        )
                    )

                    conn.commit()

                    bot.send_message(
                        user,
                        "🎉 Урок пройден! +20 XP",
                        reply_markup=menu()
                    )

                else:
                    send_question(user)

            else:

                bot.send_message(
                    user,
                    "❌ Неправильно или неизвестная команда"
                )

        else:

            bot.send_message(
                user,
                "🎉 Курс полностью завершен!"
            )



print("Bot started...")

bot.polling(none_stop=True)