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
        send = (f"Добро пожаловать, <b>{message.from_user.first_name} {message.from_user.last_name}</b>!\n"
                f"Выберите свою роль, чтобы мы могли предложить вам соответствующий функционал.")
        bot.send_message(message.chat.id, send, parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Я - Студент')  # выбрана роль студент
def clicked_role_student(message):
    if not cur.execute("""SELECT role FROM profiles WHERE id=?""", (message.chat.id,)).fetchone():
        cur.execute("""INSERT INTO profiles (id, role) VALUES(?, ?)""", (message.chat.id, roles_data['student']))
        con.commit()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Меню", callback_data='menu')
    markup.add(back_button)
    bot.send_message(message.chat.id, "Ваш профиль заполнен.", parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'clear_prof')  # забыть меня
def clear_prof(call):
    cur.execute("""DELETE FROM profiles WHERE id=?""", (call.message.chat.id,))
    con.commit()
    bot.send_message(call.message.chat.id, "Ваш профиль удален.\n"
                                           "Введите /start, чтобы начать заново.", parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'menu')  # меню
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


@bot.callback_query_handler(func=lambda call: call.data == 'get_template')  # шаблон заявления
def get_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    pic_doc = telebot.types.InlineKeyboardButton("Изображение", callback_data="pic_doc")
    file_doc = telebot.types.InlineKeyboardButton("Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(pic_doc, file_doc, back_button)
    bot.send_message(message.chat.id, "Вам достаточно изображения шаблона или нужен файл заявления?",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'pic_doc')  # изображение шаблона
def get_pic_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    file_doc = telebot.types.InlineKeyboardButton("Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(file_doc, back_button)
    bot.send_photo(message.chat.id, open("data/pics/matpomosh.png", 'rb'),
                   caption="Изображение шаблона заявления", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'file_doc')  # файл шаблона
def get_file_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    pic_doc = telebot.types.InlineKeyboardButton("Изображение", callback_data="pic_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(pic_doc, back_button)
    bot.send_document(message.chat.id, open("data/docs/matpomosh.docx", 'rb'),
                      caption="Файл шаблона завления", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_extraction')  # что такое выписка?
def get_extraction(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(back_button)
    bot.send_photo(message.chat.id, open("data/pics/vipiska.png", 'rb'),
                   caption="Вот так выглядит выписка платежа из СберБанка. "
                           "Её необходимо прикреплять к заявлению, "
                           "если оно подается на возврат средств за какую-либо покупку. "
                           "В других банках выписка выглядит аналогично.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_cats')  # категории
def get_cats(call):
    message = call.message
    bot.send_message(message.chat.id, 'BUBA')


@bot.callback_query_handler(func=lambda call: call.data == 'get_info')  # что нужно для заявления
def get_info(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    cats_button = telebot.types.InlineKeyboardButton("Категории матпомощи", callback_data='get_cats')
    file_button = telebot.types.InlineKeyboardButton("Полное положение о матпомощи", callback_data='get_mat')
    markup.add(file_button, cats_button, menu_button)
    bot.send_message(message.chat.id, "Обучающиеся ТУСУРа имеют право на получение материальной поддержки.\n"
                                      "❗<i>Из фонда деканата могут получать материальную помощь только бюджетники "
                                      "очной формы обучения.\n"
                                      "❗В деканат сдаётся готовый пакет документов: заявление → оригиналы "
                                      "подтверждающих документов (в зависимости от категории) → копии оригиналов "
                                      "подтверждающих документов (в зависимости от категории).</i>\n\n"
                                      "С 1 января 2024 года отменён налог на материальную помощь, поэтому:\n"
                                      "- ИНН не требуется;\n"
                                      "- иностранным гражданам теперь не требуется сдавать копии паспорта "
                                      "и миграционной карты.\n\n"
                                      "Правила подачи материальной помощи:\n"
                                      "1. <u>Одно заявление — один пункт положения</u>, "
                                      "в текущий месяц можно подать только одно заявление;\n"
                                      "2. В заявлении <u>необходимо указывать пункт(категорию), "
                                      "по которому оно подается</u>;\n"
                                      "3. Любые <u>чеки «действительны» только 3 месяца.</u> "
                                      "<b>Если оплата была произведена "
                                      "без кассового чека (online оплата), то необходимо приложить выписку из банка "
                                      "о том, что именно Заявитель произвёл оплату со своего счёта/карты</b>\n"
                                      "4. Стоимость билетов до дома (и обратно) будут возмещены, только если поездка "
                                      "была в каникулярное время <u>(при перелётах самолётом сохраняйте "
                                      "посадочные талоны).</u>\n\n"
                                      "❗Сроки: если пакет документов сдан до 5 числа текущего месяца, то выплата "
                                      "будет осуществлена в этом же месяце. Например, если сдали документы до "
                                      "5 апреля -> выплата будет в апреле (в день выплаты стипендий). Если сдали "
                                      "пакет документов после 5 апреля, то выплата материальной помощи будет "
                                      "осуществлена уже в мае (в день выплаты стипендий).",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_mat')  # файл положения
def get_mat(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='menu')
    markup.add(menu_button)
    bot.send_document(message.chat.id, open('data/docs/polozenie.pdf', 'rb'),
                      caption="Положение о порядке оказания материальной поддержки нуждающимся студентам и аспирантам "
                              "ТУСУРа, обучающимся по очной форме обучения за счет средств бюджетных ассигнований.",
                      reply_markup=markup)


bot.polling(none_stop=True, skip_pending=True)
