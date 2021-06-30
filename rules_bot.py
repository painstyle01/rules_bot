import telebot
import mysql.connector
from telebot import types
import logging
import time
import flask
import emoji
import re

API_TOKEN = "#"

WEBHOOK_HOST = '#'
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TOKEN)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN)

app = flask.Flask(__name__)

cnx = mysql.connector.connect(host='localhost', user='root', password='root', database='carma')
cnx.autocommit = True
cnx.close()

kb = types.ReplyKeyboardMarkup(True)
kb.row("Узнать свою карму")
kb.row("Топ 10 кармы")

text = """
Тебя приветствует команда Like Центра USA город New York !!!
Добро пожаловать в нашу семью!

Этот чат является площадкой для обмена впечатлениями, заряда вдохновением и планирования встреч.  

Чем мы будем полезны здесь?
⁃ Знакомства.
⁃ Нетворкинг участников.
- Полное ощущение присутствия.
- Консультация по курсам LIKE Центра.
- Можем дать ответы на возникающие вопросы.

В нашем чате есть несколько правил для экологичного общения.
Запрещено:

1) Объявления о продаже (в т.ч. бизнеса, франшизы, гаража, слона)
2) Ссылки на другие чаты (Или ссылки на другие ссылки:)
3) Перепродажа билетов на мероприятия и участия в курсах.
4) Спам (публикации одного и того же сообщения в чате более 2-х раз)
5) Размещение картинок и материалов 18+ (Только 18-)
6) Оскорбление других участников чата 
За это вас ждёт бан и геенна огненная.

Желаем найти тут много полезной информации, инсайтов и единомышленников. Успехов!
"""

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    print(call.from_user.id)
    print(call.data)
    if call.data != call.from_user.id:
        bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="Это не ваша кнопка")
    if call.data != call.from_user.id:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Правила приняты")
        bot.restrict_chat_member(call.message.chat.id, call.data, can_send_messages=True, can_send_polls=True, can_send_media_messages=True, can_send_other_messages=True, can_change_info=True)




@bot.message_handler(content_types=['new_chat_members'])
def new_member(message):
    member = message.new_chat_members[-1].id
    print("new member" + str(member))
    bot.restrict_chat_member(message.chat.id, member, can_send_messages=False, can_send_polls=False, can_send_media_messages=False, can_send_other_messages=False, can_change_info=False)
    keyboard = types.InlineKeyboardMarkup()
    yes_button = types.InlineKeyboardButton(text="Я прочитал и согласен с правилами.", callback_data="{}".format(member))
    keyboard.add(yes_button)
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def start(message):
    cnx.connect()
    c = cnx.cursor(buffered=True)
    print(message.from_user.id)
    c.execute("SELECT carma FROM users WHERE id='{}'".format(message.from_user.id))
    data = c.fetchone()
    print(data)
    if data is None:
        bot.send_message(message.from_user.id, "Приветствую. Ваша карма равна нулю. Что б получить карму, кому-то нужно написать в ответ на ваше сообщение \"+\"", reply_markup=kb)
        c.execute("INSERT INTO users(id,carma) VALUES('{}','0')".format(message.from_user.id))
    if data is not None:
        bot.send_message(message.from_user.id, "Приветствую. У вас {} кармы.".format(data[0]), reply_markup=kb)
    cnx.close()


@bot.message_handler(content_types=['text'])
def text(message):
    if message.chat.type == "supergroup" or message.chat.type == "group":
        if message.reply_to_message is not None:
            print(message.text)
            txt = emoji.demojize(message.text)
            print(txt)
            r = re.search(":thumbs_up_light_skin_tone:|:thumbs_up_medium-light_skin_tone:|:thumbs_up_medium_skin_tone:|:thumbs_up_medium-dark_skin_tone:|:thumbs_up_dark_skin_tone:|:thumbsup:", txt)
            print(r)
            if r is not None:
                cnx.connect()
                c = cnx.cursor(buffered=True)
                c.execute("SELECT carma FROM users WHERE id='{}'".format(message.reply_to_message.from_user.id))
                data = c.fetchone()
                if data is None:
                    c.execute("INSERT INTO users(id,carma) VALUES('{}','1')".format(message.reply_to_message.from_user.id))
                    bot.reply_to(message, "{} ===> +1 {} (1)".format(message.from_user.first_name, message.reply_to_message.from_user.first_name))
                else:
                    if message.reply_to_message.from_user.id == message.from_user.id:
                        pass
                    else:
                        new_carma = int(data[0]) + 1
                        c.execute("UPDATE users SET carma='{}' WHERE id='{}'".format(new_carma, message.reply_to_message.from_user.id))
                        bot.reply_to(message, "{} ===> +1 {} ({})".format(message.from_user.first_name,
                                                                   message.reply_to_message.from_user.first_name, new_carma))
                cnx.close()
    if message.chat.type == 'private':
        cnx.connect()
        c = cnx.cursor(buffered=True)
        if message.text == "Узнать свою карму":
            c.execute("SELECT carma FROM users WHERE id='{}'".format(message.from_user.id))
            data = c.fetchone()[0]
            bot.send_message(message.from_user.id, "Ваша карма: {}".format(data))
        if message.text == "Топ 10 кармы":
            c.execute("SELECT carma, id FROM users ORDER BY carma DESC LIMIT 10")
            data = c.fetchall()
            str = ""
            for strings in data:
                print(strings)
                str += "Пользователь [{}](tg://user?id={}) : {} кармы\n".format(strings[1],strings[1],strings[0])
            print(str)
            bot.send_message(message.from_user.id, str, parse_mode="Markdown")
            cnx.close()

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

time.sleep(1)

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Start flask server
app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        debug=True)