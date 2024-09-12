import datetime as dt
import logging
import sqlite3

import telebot

con = sqlite3.connect("data/data.sqlite", check_same_thread=False)
cur = con.cursor()
roles_data = {f'{x[1]}': x[0] for x in cur.execute("""SELECT number, name FROM roles""").fetchall()}  # all roles dict

logger = telebot.logger  # logging all actions
telebot.logger.setLevel(logging.DEBUG)  # outputs debug messages to console.

bot = telebot.TeleBot('7288916895:AAEi8SpPF_XlNXwQRWeabaPo_MjLpnaKB9A')  # https://t.me/MatAidTUSURbot

splitter = "@%$"  # splits updates on question and answer in msg (check DB for details)
passwd = '*&TUSURuniversityMatAidBotEmpoyee@!**'

cats = [x for x in open('data/text/cats.txt', 'r', encoding='utf-8').read().split(splitter)]
statuses = {1: '⚠️', 2: '✅'}


@bot.message_handler(commands=['start'])  # регистрация / вход (если пользователь записан)
def start(message):
    role = cur.execute("""SELECT role FROM profiles WHERE id=(?)""", (message.chat.id,)).fetchone()
    if role:  # user has role
        markup = telebot.types.InlineKeyboardMarkup()
        if role[0] == 2:
            back_button = telebot.types.InlineKeyboardButton("Меню", callback_data='employee_menu')
        else:
            back_button = telebot.types.InlineKeyboardButton("Меню", callback_data='student_menu')
        markup.add(back_button)
        send = f"Здравствуйте, <b>{message.from_user.first_name} {message.from_user.last_name}</b>."

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
    back_button = telebot.types.InlineKeyboardButton("Меню", callback_data='student_menu')
    markup.add(back_button)

    bot.send_message(message.chat.id, "Ваш профиль создан.", parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Я - Сотрудник')  # выбрана роль сотрудник
def clicked_role_employee(message):
    bot.send_message(message.chat.id, "Введите ключ, чтобы создать профиль сотрудника или выполнить вход:",
                     parse_mode='html')

    bot.register_next_step_handler_by_chat_id(message.chat.id, create_employee)


def create_employee(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Меню", callback_data='employee_menu')
    if message.text == passwd:
        markup.add(back_button)
        if not cur.execute("""SELECT role FROM profiles WHERE id=?""", (message.chat.id,)).fetchone():
            cur.execute("""INSERT INTO profiles (id, role) VALUES(?, ?)""",
                        (message.chat.id, roles_data['employee']))
            con.commit()
            bot.send_message(message.chat.id, "Профиль успешно создан!", parse_mode='html', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Ваш профиль уже существует. Вход успешно выполнен.",
                             parse_mode='html', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Неверный ключ. Введите /start, чтобы начать заново.",
                         parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'clear_prof')  # забыть меня
def clear_prof(call):
    cur.execute("""DELETE FROM profiles WHERE id=?""", (call.message.chat.id,))
    con.commit()

    bot.send_message(call.message.chat.id, "Ваш профиль удален.\n"
                                           "Введите /start, чтобы начать заново.", parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'student_menu')  # меню
def callstudent_menu_student(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    clear_button = telebot.types.InlineKeyboardButton("Забыть меня", callback_data="clear_prof")
    extr_button = telebot.types.InlineKeyboardButton("Как выглядит выписка?", callback_data="get_extraction")
    info_button = telebot.types.InlineKeyboardButton("Что нужно для оформления матпомощи?", callback_data="get_info")
    template_button = telebot.types.InlineKeyboardButton("Шаблон заявления", callback_data="get_template")
    categories_button = telebot.types.InlineKeyboardButton("Категории матпомощи", callback_data="get_cats")
    help_button = telebot.types.InlineKeyboardButton("Помощь", callback_data="get_help")
    markup.add(info_button, extr_button, template_button, categories_button, help_button, clear_button)

    bot.send_message(message.chat.id, f"Студент, вам доступны следующие функции:",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_template')  # шаблон заявления
def get_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    pic_doc = telebot.types.InlineKeyboardButton("Изображение", callback_data="pic_doc")
    file_doc = telebot.types.InlineKeyboardButton("Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='student_menu')
    markup.add(pic_doc, file_doc, back_button)

    bot.send_message(message.chat.id, "Вам достаточно изображения шаблона или нужен файл заявления?",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'pic_doc')  # изображение шаблона
def get_pic_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    file_doc = telebot.types.InlineKeyboardButton("Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_template')
    markup.add(file_doc, back_button)

    bot.send_photo(message.chat.id, open("data/pics/matpomosh.png", 'rb'),
                   caption="Изображение шаблона заявления", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'file_doc')  # файл шаблона
def get_file_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    pic_doc = telebot.types.InlineKeyboardButton("Изображение", callback_data="pic_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_template')
    markup.add(pic_doc, back_button)

    bot.send_document(message.chat.id, open("data/docs/matpomosh.docx", 'rb'),
                      caption="Файл шаблона завления", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_extraction')  # что такое выписка?
def get_extraction(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='student_menu')
    markup.add(back_button)

    bot.send_photo(message.chat.id, open("data/pics/vipiska.png", 'rb'),
                   caption="Вот так выглядит выписка платежа из СберБанка. "
                           "Её необходимо прикреплять к заявлению, "
                           "если оно подается на возврат средств за какую-либо покупку. "
                           "В других банках выписка выглядит аналогично.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_cats')  # категории
def get_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    back_button = telebot.types.InlineKeyboardButton("Назад",
                                                     callback_data='get_info')
    family_button = telebot.types.InlineKeyboardButton("Семья",
                                                       callback_data='family_cats')
    life_button = telebot.types.InlineKeyboardButton("Жизненная ситуация",
                                                     callback_data='life_cats')
    soc_button = telebot.types.InlineKeyboardButton("Соц статус",
                                                    callback_data='social_cats')
    pay_button = telebot.types.InlineKeyboardButton("Покупки",
                                                    callback_data='pay_cats')
    allcats_button = telebot.types.InlineKeyboardButton("Все категории", callback_data='all_cats')
    cond_button = telebot.types.InlineKeyboardButton("Условия предоставления матпомощи",
                                                     callback_data='conditions')
    file_button = telebot.types.InlineKeyboardButton("Полное положение о матпомощи", callback_data='get_mat')
    markup.add(family_button, life_button, soc_button, pay_button, allcats_button)
    markup.add(cond_button)
    markup.add(file_button)
    markup.add(back_button)

    bot.send_message(message.chat.id, "Ниже вы можете выбрать конкретную логическую группу категорий "
                                      "или посмотреть сразу все. Напоминаем, что <u> полный список категорий "
                                      f"и условий также представлен в тексте полного "
                                      f"положения о матпомощи.</u>\n\n"
                                      f"{cats[0]}",
                     parse_mode='html',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'all_cats')  # категории
def all_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    markup.add(back_button)

    text_msg = [x for x in cats[1].split('*')]
    for i in range(3):
        if i == 2:
            bot.send_message(message.chat.id, text_msg[i], parse_mode='html', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text_msg[i], parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'family_cats')  # категории
def family_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[2], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'life_cats')  # категории
def life_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[3], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'social_cats')  # категории
def social_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[4], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'pay_cats')  # категории
def pay_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[5], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'conditions')  # условия
def conditions(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    markup.add(back_button)

    bot.send_photo(message.chat.id, open('data/pics/kvartal.jpg', 'rb'))
    bot.send_message(message.chat.id, cats[6], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_info')  # что нужно для заявления
def get_info(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='student_menu')
    cats_button = telebot.types.InlineKeyboardButton("Категории матпомощи", callback_data='get_cats')
    file_button = telebot.types.InlineKeyboardButton("Полное положение о матпомощи", callback_data='get_mat')
    markup.add(file_button, cats_button, student_menu_button)

    bot.send_message(message.chat.id, "Обучающиеся ТУСУРа имеют право на получение материальной поддержки.\n"
                                      "❗<i>Из фонда деканата могут получать "
                                      "материальную помощь только бюджетники "
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
                                      "без кассового чека (online оплата), "
                                      "то необходимо приложить выписку из банка "
                                      "о том, что именно Заявитель произвёл оплату со своего счёта/карты</b>\n"
                                      "4. Стоимость билетов до дома (и обратно) "
                                      "будут возмещены, только если поездка "
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
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='student_menu')
    markup.add(student_menu_button)

    bot.send_document(message.chat.id, open('data/docs/polozenie.pdf', 'rb'),
                      caption="Положение о порядке оказания материальной поддержки "
                              "нуждающимся студентам и аспирантам "
                              "ТУСУРа, обучающимся по очной форме обучения "
                              "за счет средств бюджетных ассигнований.",
                      reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_help')
def get_help(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    ask_button = telebot.types.InlineKeyboardButton("❓ Задать вопрос", callback_data='send_question')
    memory_button = telebot.types.InlineKeyboardButton("⏰ Архив", callback_data='memory')
    clean_button = telebot.types.InlineKeyboardButton("Очистить архив", callback_data='clean_memory')
    student_menu_button = telebot.types.InlineKeyboardButton("Меню", callback_data='student_menu')
    markup.add(ask_button, memory_button, clean_button)
    markup.add(student_menu_button)

    bot.send_message(message.chat.id, "Выберите, какое действие вы хотите совершить:\n"
                                      "<i>Задать вопрос</i> - отправить вопрос сотруднику. "
                                      "Незакрытые вопросы объединяются в одну цепочку, "
                                      "поэтому не забывайте отмечать решенные вопросы в "
                                      "архиве соответствующим статусом.\n"
                                      "<i>Архив</i> - содержит ваши вопросы, их "
                                      "статусы и ответы сотрудника, если они есть.",
                     parse_mode='html',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'send_question')
def send_question(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Меню", callback_data='student_menu')
    bot.send_message(message.chat.id, "Напишите в одном сообщении суть вопроса. "
                                      "Если необходимо прикрепить какие-либо файлы, "
                                      "то сохраните их в облаке и оставьте в вопросе ссылку.",
                     reply_markup=markup)
    markup.add(student_menu_button)

    bot.register_next_step_handler_by_chat_id(message.chat.id, save_question)


def save_question(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_help')
    markup.add(student_menu_button)
    id_user, text, date = message.chat.id, message.text, dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S%z")
    talkid_open = cur.execute("""SELECT talk_id, from_user FROM messages WHERE status=(?) AND user_id=(?)""",
                              (1, id_user)).fetchone()
    if not talkid_open:  # new question
        cur.execute("""INSERT INTO messages (from_user, user_id, date, status) VALUES(?, ?, ?, ?)""",
                    (text, id_user, date, 1))

        bot.send_message(message.chat.id, "Сообщение отправлено сотруднику. Ожидайте ответа.",
                         reply_markup=markup)
    else:  # update old question
        cur.execute("""UPDATE messages SET from_user=(?) WHERE user_id=(?) AND status=(?)""",
                    (talkid_open[1] + "\n<i>UPD: </i>" + text, id_user, 1))

        bot.send_message(message.chat.id, "Ваш открытый вопрос дополнен. Ожидайте ответа.",
                         reply_markup=markup, parse_mode='html')
    con.commit()


@bot.callback_query_handler(func=lambda call: call.data == 'memory')
def memory(call):
    message = call.message
    all_msgs = cur.execute("SELECT date, status FROM messages WHERE user_id=(?)",
                           (message.chat.id,)).fetchall()
    all_msgs.sort(key=lambda x: x[1], reverse=True)

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    btns_closed = [telebot.types.InlineKeyboardButton(text=f"{statuses[x[1]]} {x[0]} ", callback_data=f"get_msg_{x[0]}")
                   for x in all_msgs]
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_help')
    markup.add(*btns_closed)
    markup.add(student_menu_button)

    bot.send_message(message.chat.id, "⚠️ - Вопрос открыт\n"
                                      "✅ - Вопрос закрыт\n\n"
                                      "Выберите время отправки вопроса:", reply_markup=markup, parse_mode='html')


@bot.callback_query_handler(func=lambda call: 'get_msg_' in call.data)
def get_msg(call):
    message = call.message
    total_msg = cur.execute(
        """SELECT from_user, to_user, status, talk_id FROM messages WHERE user_id=(?) AND date=(?)""",
        (message.chat.id, call.data.split("_")[-1])).fetchone()
    user_msg = total_msg[0].split(splitter)
    answer_msg = total_msg[1].split(splitter) if total_msg[1] else []

    msg_text = f"Статус вопроса: {'Вопрос открыт' if total_msg[2] == 1 else 'Вопрос закрыт'}\n\n"
    for i in range(len(user_msg)):
        msg_text += f'<b>Часть вопроса №{i + 1}.</b> {user_msg[i]}\n\n'
        if i < len(answer_msg):
            msg_text += f'<b>Ответ сотрудника: </b><i>{answer_msg[i]}</i>\n\n' \
                if answer_msg[i] else '<b>Ответ сотрудника: </b><i>Сотрудник еще не ответил.</i>'

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='memory')
    close_button = telebot.types.InlineKeyboardButton("Вопрос решен", callback_data=f'close_msg_{total_msg[3]}')
    markup.add(close_button, student_menu_button) if total_msg[2] == 1 else markup.add(student_menu_button)

    bot.send_message(message.chat.id, msg_text, reply_markup=markup, parse_mode='html')


@bot.callback_query_handler(func=lambda call: 'close_msg_' in call.data)
def close_question(call):
    message = call.message

    cur.execute("""UPDATE messages SET status=(?) WHERE talk_id=(?)""", (2, call.data.split('_')[-1]))
    con.commit()

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='memory')
    markup.add(student_menu_button)

    bot.send_message(message.chat.id, "Вопрос успешно закрыт!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'clean_memory')
def clean_memory(call):
    message = call.message

    cur.execute("""DELETE FROM messages WHERE user_id=(?)""", (message.chat.id,))
    con.commit()

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_help')
    markup.add(student_menu_button)

    bot.send_message(message.chat.id, "Архив успешно очищен!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'employee_menu')
def employee_menu(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    clear_button = telebot.types.InlineKeyboardButton("Забыть меня", callback_data="clear_prof")
    global_button = telebot.types.InlineKeyboardButton("Отправить глобальное сообщение", callback_data="global_send")
    helpst_button = telebot.types.InlineKeyboardButton("Вопросы студентов", callback_data="help_student")
    students_menu = telebot.types.InlineKeyboardButton("Меню для студентов", callback_data="student_menu")
    markup.add(global_button, students_menu, helpst_button, clear_button)

    bot.send_message(message.chat.id, f"Сотрудник, вам доступны следующие функции:",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'global_send')  # func for employees
def global_send(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    employee_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='employee_menu')
    bot.send_message(message.chat.id, "Напишите глобальное сообщение, "
                                      "оно будет отправлено через бота всем студентам. Если нужно прикрепить файл, "
                                      "загрузите его в облако и оставьте в сообщении ссылку\n\n"
                                      "Можно использовать html теги для текста. Например:\n"
                                      "<b>текст</b> - жирный текст\n"
                                      "<i>текст</i> - курсив\n"
                                      "<u>текст</u> - подчеркнутый",
                     reply_markup=markup)
    markup.add(employee_menu_button)

    bot.register_next_step_handler_by_chat_id(message.chat.id, send_global_msg)


def send_global_msg(message):  # sending func from global_send
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    employee_menu_button = telebot.types.InlineKeyboardButton("Меню", callback_data='employee_menu')
    markup.add(employee_menu_button)

    shadow_markup = telebot.types.InlineKeyboardMarkup(row_width=1)  # markup for students
    student_menu_button = telebot.types.InlineKeyboardButton("Меню", callback_data='student_menu')
    shadow_markup.add(student_menu_button)

    ids = cur.execute("""SELECT id FROM profiles WHERE
                      role=(SELECT number FROM roles WHERE name='student')""").fetchall()[0]
    textlist = telebot.util.smart_split(message.text, 3000)
    for id_students in ids:
        for count, msg in enumerate(textlist):
            if count == 0:
                bot.send_message(id_students, f"<b><i>Глобальное сообщение от сотрудника:</i></b>\n\n{msg}",
                                 parse_mode='html', reply_markup=shadow_markup if len(textlist) <= 1 else None)
            else:
                bot.send_message(id_students, f"{msg}",
                                 parse_mode='html', reply_markup=shadow_markup)
    bot.send_message(message.chat.id, f"Сообщение успешно отправлено!",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'help_student')
def questions_menu(call):
    pass


bot.infinity_polling(skip_pending=True)
