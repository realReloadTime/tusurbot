import telebot
import logging
import sqlite3

con = sqlite3.connect("data/data.sqlite", check_same_thread=False)
cur = con.cursor()
roles_data = {f'{x[1]}': x[0] for x in cur.execute("""SELECT number, name FROM roles""").fetchall()}  # all roles dict

logger = telebot.logger  # logging all actions
telebot.logger.setLevel(logging.DEBUG)  # outputs debug messages to console.

bot = telebot.TeleBot('7288916895:AAEi8SpPF_XlNXwQRWeabaPo_MjLpnaKB9A')  # https://t.me/MatAidTUSURbot


@bot.message_handler(commands=['start'])  # регистрация / вход (если пользователь записан)
def start(message):
    role = cur.execute("""SELECT role FROM profiles WHERE id=(?)""", (message.chat.id,)).fetchone()
    if role:  # user has role
        markup = telebot.types.InlineKeyboardMarkup()
        back_button = telebot.types.InlineKeyboardButton("Меню", callback_data='menu')
        markup.add(back_button)
        send = f"Здравствуйте, <b>{message.from_user.first_name} {message.from_user.last_name}</b>"
        bot.send_message(message.chat.id, send, parse_mode='html', reply_markup=markup)
    else:  # user is new
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        student_button = telebot.types.KeyboardButton("Я - Студент")
        employee_button = telebot.types.KeyboardButton("Я - Сотрудник")
        markup.add(student_button, employee_button)
        send = f"Добро пожаловать, <b>{message.from_user.first_name} {message.from_user.last_name}</b>"
        bot.send_message(message.chat.id, send, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Я - Студент')
def clicked_role_student(message):
    if not cur.execute("""SELECT role FROM profiles WHERE id=?""", (message.chat.id,)).fetchone():
        cur.execute("""INSERT INTO profiles (id, role) VALUES(?, ?)""", (message.chat.id, roles_data['student']))
        con.commit()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(back_button)
    bot.send_message(message.chat.id, "Ваш профиль заполнен.", parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'clear_prof')
def clear_prof(call):
    cur.execute("""DELETE FROM profiles WHERE id=?""", (call.message.chat.id,))
    con.commit()
    bot.send_message(call.message.chat.id, "Ваш профиль удален.\n"
                                           "Введите /start, чтобы начать заново.", parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'menu')
def callmenu_student(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    clear_button = telebot.types.InlineKeyboardButton("Забыть меня", callback_data="clear_prof")
    extr_button = telebot.types.InlineKeyboardButton("Как выглядит выписка?", callback_data="get_extraction")
    info_button = telebot.types.InlineKeyboardButton("Что нужно для оформления матпомощи?", callback_data="get_info")
    template_button = telebot.types.InlineKeyboardButton("Шаблон заявления", callback_data="get_template")
    categories_button = telebot.types.InlineKeyboardButton("Категории матпомощи", callback_data="get_cats")
    markup.add(info_button, extr_button, template_button, categories_button, clear_button)
    bot.send_message(message.chat.id, f"Студент, вам доступны следующие функции:",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_template')
def get_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    pic_doc = telebot.types.InlineKeyboardButton("Изображение", callback_data="pic_doc")
    file_doc = telebot.types.InlineKeyboardButton("Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(pic_doc, file_doc, back_button)
    bot.send_message(message.chat.id, "Вам достаточно изображения шаблона или нужен файл заявления?",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'pic_doc')
def get_pic_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    file_doc = telebot.types.InlineKeyboardButton("Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(file_doc, back_button)
    bot.send_photo(message.chat.id, open("data/pics/matpomosh.png", 'rb'), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'file_doc')
def get_file_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    pic_doc = telebot.types.InlineKeyboardButton("Изображение", callback_data="pic_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(pic_doc, back_button)
    bot.send_document(message.chat.id, open("data/docs/matpomosh.docx", 'rb'), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_extraction')
def get_extraction(call):
    message = call.message
    bot.send_photo(message.chat.id, open("data/pics/vipiska.png", 'rb'))


bot.polling(none_stop=True)
