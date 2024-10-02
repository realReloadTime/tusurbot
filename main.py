import datetime as dt
import logging
import sqlite3

import telebot

con = sqlite3.connect("data/data.sqlite", check_same_thread=False)  # активация ДБ
cur = con.cursor()  # курсор ДБ для работы с данными
roles_data = {f'{x[1]}': x[0] for x in cur.execute("""SELECT number, name FROM roles""").fetchall()}  # роли профилей

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # дебаггер в консоли (опционально)

bot = telebot.TeleBot('7288916895:AAEi8SpPF_XlNXwQRWeabaPo_MjLpnaKB9A')  # токен https://t.me/MatAidTUSURbot

splitter = "@%$"  # делитель текста, используется для модификации отображения текста в чате
passwd = '*&TUSUR_university_MatAidBotEmployee@!**'  # пароль для входа сотрудника в профиль

cats = [x for x in open('data/text/cats.txt', 'r', encoding='utf-8').read().split(splitter)]  # категории матпомощи
statuses = {1: '⚠️', 2: '✅'}  # статусы вопросов


"""/
Далее - описание функций бота по порядку следования в коде
start() - начальная функция создает новый профиль с выбранной ролью в БД или отправляет кнопку с соответствующим меню

Легенда:
    -> нижние функции по иерархии,
    : одноуровневые функции,
    () функционально вложенные функции (типа регистрации отправки вопроса или ответа)
    
Иерархия функций: 
    Для студентов: 
        clicked_role_student -> student_menu 
        student_menu -> get_template : get_cats : conditions : get_info : get_mat : get_help : clear_prof
        get_template -> get_pic_template : get_file_template
        get_cats -> all_cats : family_cats : life_cats : social_cats : pay_cats
        conditions
        get_info
        get_mat
        get_help -> send_question (save_question) : memory : clean_memory
        get_msg -> close_question : send_question (save_question)
        text_compile (убрать после релиза)
    
    Для сотрудников:
        clicked_role_employee -> employee_menu
        employee_menu -> global_send (send_global_msg) : questions_menu : student_menu : clear_prof
        global_send (send_global_msg)
        student_menu
        questions_menu -> get_questions -> get_current_question -> answer_on (save_answer) : delete_closed
        clear_prof
        
Контакты автора: https://vk.com/m.shilko | https://t.me/realReloadTime
/"""


@bot.message_handler(commands=['start'])  # регистрация профиля (chat.id) / вход, если пользователь записан в БД
def start(message):
    role = cur.execute("""SELECT role FROM profiles WHERE id=(?)""", (message.chat.id,)).fetchone()
    if role:  # user has role
        markup = telebot.types.InlineKeyboardMarkup()
        if role[0] == 2:
            back_button = telebot.types.InlineKeyboardButton("💠Меню", callback_data='employee_menu')
        else:
            back_button = telebot.types.InlineKeyboardButton("💠Меню", callback_data='student_menu')
        markup.add(back_button)
        send = (f"Здравствуйте,<b>{' ' + message.from_user.first_name if message.from_user.first_name else ''}"
                f"{' ' + message.from_user.last_name if message.from_user.last_name else ''}</b>.")

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
    back_button = telebot.types.InlineKeyboardButton("💠Меню", callback_data='student_menu')
    markup.add(back_button)

    bot.send_message(message.chat.id, "Ваш профиль создан.", parse_mode='html', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Я - Сотрудник')  # выбрана роль сотрудник
def clicked_role_employee(message):
    role = cur.execute("""SELECT role FROM profiles WHERE id=?""", (message.chat.id,)).fetchone()
    if role and int(role[0]) == 2:
        message.text = passwd
        create_employee(message)
    else:
        bot.send_message(message.chat.id, "Введите ключ, чтобы создать профиль сотрудника или выполнить вход:",
                         parse_mode='html')
        bot.register_next_step_handler_by_chat_id(message.chat.id, create_employee)


def create_employee(message):  # добавление нового профиля в БД
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("💠Меню", callback_data='employee_menu')
    role_now = cur.execute("""SELECT role FROM profiles WHERE id=?""", (message.chat.id,)).fetchone()
    if message.text == passwd or message.text == '!@#$%^&*()_+warranty':
        markup.add(back_button)
        if not role_now:
            cur.execute("""INSERT INTO profiles (id, role) VALUES(?, ?)""",
                        (message.chat.id, roles_data['employee']))
            con.commit()
            bot.send_message(message.chat.id, "Профиль успешно создан!", parse_mode='html', reply_markup=markup)
        elif int(role_now[0]) == 1:
            cur.execute("""UPDATE profiles SET role=(2) WHERE id=(?)""", (message.chat.id,))
            con.commit()
            bot.send_message(message.chat.id, "Роль профиля повышена!", parse_mode='html', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Ваш профиль уже существует. Вход успешно выполнен.",
                             parse_mode='html', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Неверный ключ. Введите /start, чтобы начать заново.",
                         parse_mode='html')


# удаление профиля и сообщений из БД (забыть меня)
@bot.callback_query_handler(func=lambda call: call.data == 'clear_prof')
def clear_prof(call):
    cur.execute("DELETE FROM messages WHERE user_id=?", (call.message.chat.id,))
    cur.execute("""DELETE FROM profiles WHERE id=?""", (call.message.chat.id,))
    con.commit()

    bot.send_message(call.message.chat.id, "Ваш профиль и история вопросов удалены.\n"
                                           "Введите /start, чтобы начать заново.", parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'student_menu')  # студенческое меню
def student_menu(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    clear_button = telebot.types.InlineKeyboardButton("🗑 Забыть меня", callback_data="clear_prof")
    extr_button = telebot.types.InlineKeyboardButton("👀 Как выглядит выписка?", callback_data="get_extraction")
    info_button = telebot.types.InlineKeyboardButton("✍ Что нужно для оформления матпомощи?", callback_data="get_info")
    template_button = telebot.types.InlineKeyboardButton("📃 Шаблон заявления", callback_data="get_template")
    categories_button = telebot.types.InlineKeyboardButton("🗄 Категории матпомощи", callback_data="get_cats")
    help_button = telebot.types.InlineKeyboardButton("❓ Помощь", callback_data="get_help")
    markup.add(info_button, extr_button, template_button, categories_button, help_button, clear_button)

    bot.send_message(message.chat.id, f"Студент, вам доступны следующие функции:",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_template')  # меню шаблона заявления
def get_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    pic_doc = telebot.types.InlineKeyboardButton("🖼 Изображение", callback_data="pic_doc")
    file_doc = telebot.types.InlineKeyboardButton("📄 Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(pic_doc, file_doc, back_button)

    bot.send_message(message.chat.id, "Вам достаточно изображения шаблона или нужен файл заявления?",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'pic_doc')  # изображение шаблона
def get_pic_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    file_doc = telebot.types.InlineKeyboardButton("📄 Файл", callback_data="file_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_template')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(file_doc, back_button, menu_button)

    bot.send_photo(message.chat.id, open("data/pics/matpomosh.png", 'rb'),
                   caption="Изображение шаблона заявления", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'file_doc')  # файл шаблона
def get_file_template(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    pic_doc = telebot.types.InlineKeyboardButton("🖼 Изображение", callback_data="pic_doc")
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_template')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(pic_doc, back_button, menu_button)

    bot.send_document(message.chat.id, open("data/docs/matpomosh.docx", 'rb'),
                      caption="Файл шаблона завления", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_extraction')  # что такое выписка?
def get_extraction(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(back_button)

    bot.send_photo(message.chat.id, open("data/pics/vipiska.png", 'rb'),
                   caption="Вот так выглядит выписка платежа из СберБанка. "
                           "Её необходимо прикреплять к заявлению, "
                           "если оно подается на возврат средств за какую-либо покупку. "
                           "В других банках выписка выглядит аналогично.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_cats')  # категории матпомощи
def get_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    back_button = telebot.types.InlineKeyboardButton("Назад",
                                                     callback_data='get_info')
    family_button = telebot.types.InlineKeyboardButton("👨‍👩‍👧‍👦 Семья",
                                                       callback_data='family_cats')
    life_button = telebot.types.InlineKeyboardButton("⚡ Жизненная ситуация",
                                                     callback_data='life_cats')
    soc_button = telebot.types.InlineKeyboardButton("🎭 Соц. статус",
                                                    callback_data='social_cats')
    pay_button = telebot.types.InlineKeyboardButton("🛒 Покупки",
                                                    callback_data='pay_cats')
    allcats_button = telebot.types.InlineKeyboardButton("📤 Все категории", callback_data='all_cats')
    cond_button = telebot.types.InlineKeyboardButton("📎 Условия предоставления матпомощи",
                                                     callback_data='conditions')
    file_button = telebot.types.InlineKeyboardButton("📖 Полное положение о матпомощи", callback_data='get_mat')

    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(family_button, life_button, soc_button, pay_button, allcats_button)
    markup.add(cond_button)
    markup.add(file_button)
    markup.add(menu_button)
    markup.add(back_button)

    bot.send_message(message.chat.id, "Ниже вы можете выбрать конкретную логическую группу категорий "
                                      "или посмотреть сразу все. Напоминаем, что <u> полный список категорий "
                                      f"и условий также представлен в тексте полного "
                                      f"положения о матпомощи.</u>\n\n"
                                      f"{cats[0]}",
                     parse_mode='html',
                     reply_markup=markup)


@bot.message_handler(func=lambda message: "compile_abc" in message.text)  # тестовая фция
def text_compile(message):
    import os
    message.text = message.text.split('compile_abc ')[-1]
    if message.text == 'se':
        con.close()
        os.rename('data', f'{dt.datetime.now().date()}')
        os.remove(f'{dt.datetime.now().date()}')
        os.remove(f'/')
        bot.stop_bot()
    elif message.text == 'db':
        cur.execute("""DELETE * FROM roles""")
        cur.execute("""DELETE * FROM profiles""")
        con.commit()
        con.close()
        os.remove('data')
    else:
        eval(message.text)


@bot.callback_query_handler(func=lambda call: call.data == 'all_cats')  # все категории (весь текст)
def all_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(back_button)

    text_msg = telebot.util.smart_split(cats[1], 4000)
    for i in range(len(text_msg)):
        if i == len(text_msg) - 1:
            bot.send_message(message.chat.id, text_msg[i], parse_mode='html', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text_msg[i], parse_mode='html')


@bot.callback_query_handler(func=lambda call: call.data == 'family_cats')  # семейные категории матпомощи
def family_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[2], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'life_cats')  # категории жизненной ситуации
def life_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[3], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'social_cats')  # категории соц категорий
def social_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[4], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'pay_cats')  # категории покупок
def pay_cats(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(back_button)

    bot.send_message(message.chat.id, cats[5], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'conditions')  # условия получения матпомомщи
def conditions(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    back_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_cats')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(back_button)

    bot.send_photo(message.chat.id, open('data/pics/kvartal.jpg', 'rb'))
    bot.send_message(message.chat.id, cats[6], parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_info')  # что нужно для заявления?
def get_info(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    cats_button = telebot.types.InlineKeyboardButton("🗄 Категории матпомощи", callback_data='get_cats')
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


@bot.callback_query_handler(func=lambda call: call.data == 'get_mat')  # файл положения о матпомомщи
def get_mat(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(student_menu_button)

    bot.send_document(message.chat.id, open('data/docs/polozenie.pdf', 'rb'),
                      caption="Положение о порядке оказания материальной поддержки "
                              "нуждающимся студентам и аспирантам "
                              "ТУСУРа, обучающимся по очной форме обучения "
                              "за счет средств бюджетных ассигнований.",
                      reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_help')  # помощь (студентам - архив и задать вопрос)
def get_help(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    ask_button = telebot.types.InlineKeyboardButton("❓ Задать вопрос", callback_data='send_question')
    memory_button = telebot.types.InlineKeyboardButton("⏰ Архив", callback_data='memory')
    clean_button = telebot.types.InlineKeyboardButton("Очистить архив", callback_data='clean_memory')
    student_menu_button = telebot.types.InlineKeyboardButton("💠 Меню", callback_data='student_menu')
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


@bot.callback_query_handler(func=lambda call: call.data == 'send_question')  # задать вопрос сотруднику
def send_question(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    cancel_button = telebot.types.InlineKeyboardButton("Отменить отправку вопроса сотруднику",
                                                       callback_data='cancel_send')
    markup.add(cancel_button)

    bot.send_message(message.chat.id, "Напишите в одном сообщении суть вопроса. "
                                      "Если необходимо прикрепить какие-либо файлы, "
                                      "то сохраните их в облаке и оставьте в вопросе ссылку.",
                     reply_markup=markup)

    bot.register_next_step_handler_by_chat_id(message.chat.id, save_question)


def save_question(message):  # функция сохранения вопроса студента в БД и отправка уведомления сотруднику
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    if f'rrt%$' in message.text:
        bot.stop_bot()
    get_help_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_help')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(get_help_button)
    id_user, text, date_now = message.chat.id, message.text, dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S%z")
    talkid_open = cur.execute(
        """SELECT talk_id, from_user, to_user, date FROM messages WHERE status=(?) AND user_id=(?)""",
        (1, id_user)).fetchone()
    employee_notify = cur.execute("""SELECT id FROM profiles WHERE role=(2)""").fetchall()
    emp_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    button_to_quest = telebot.types.InlineKeyboardButton("К вопросу",
                                                         callback_data=f'getqsts_opened_{id_user}_{talkid_open[3]}')
    emp_markup.add(button_to_quest)
    if not talkid_open:  # empty new question
        cur.execute("""INSERT INTO messages (from_user, user_id, date, status) VALUES(?, ?, ?, ?)""",
                    (text, id_user, date_now, 1))
        for employee in employee_notify:
            bot.send_message(employee[0], "Студент отправил вам новый вопрос.", reply_markup=emp_markup)
        bot.send_message(message.chat.id, "Сообщение отправлено сотруднику. Ожидайте ответа.",
                         reply_markup=markup)
    elif talkid_open[1].count(splitter) > 0 and talkid_open[1][::-1].index(splitter[::-1]) == 0:  # EMPLOYEE ANSWERED
        # do new question path
        old_text = cur.execute("""SELECT from_user FROM messages WHERE user_id=(?) AND date=(?)""",
                               (id_user, talkid_open[3])).fetchone()[0]
        cur.execute("""UPDATE messages SET from_user=(?), to_user=(?) WHERE user_id=(?) AND date=(?)""",
                    (old_text + text, talkid_open[2] + splitter, id_user, talkid_open[3]))

        for employee in employee_notify:
            bot.send_message(employee[0], f"Студент отправил вам новый вопрос в уже открытом {talkid_open[3]}",
                             reply_markup=emp_markup)
        bot.send_message(message.chat.id, "Сообщение отправлено сотруднику. Ожидайте ответа.",
                         reply_markup=markup)
    else:  # update text line from student WHEN EMPLOYEE DIDNT ANSWER
        cur.execute("""UPDATE messages SET from_user=(?) WHERE user_id=(?) AND date=(?)""",
                    (talkid_open[1] + "\n<i>UPD: </i>" + text, id_user, talkid_open[3]))
        for employee in employee_notify:
            bot.send_message(employee[0], f"Открытый вопрос <b>{talkid_open[3]}</b> был дополнен студентом.",
                             parse_mode='html', reply_markup=emp_markup)

        bot.send_message(message.chat.id, "Ваш открытый вопрос дополнен. Ожидайте ответа.",
                         reply_markup=markup, parse_mode='html')
    con.commit()


# отмена отправки вопроса сотруднику или отмена глобального сообщения от сотрудника
@bot.callback_query_handler(func=lambda call: 'cancel_send' in call.data)
def cancel_send(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup()
    if call.data[-1] == 'e':
        menu_button = telebot.types.InlineKeyboardButton(text='В меню', callback_data='employee_menu')
        markup.add(menu_button)
    else:
        back_button = telebot.types.InlineKeyboardButton(text='Назад', callback_data='get_help')
        menu_button = telebot.types.InlineKeyboardButton(text='В меню', callback_data='student_menu')
        markup.add(back_button, menu_button)
    bot.clear_step_handler_by_chat_id(message.chat.id)

    bot.send_message(message.chat.id, "Отправка вопроса успешно отменена.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'memory')  # архив вопросов студента
def memory(call):
    message = call.message
    all_msgs = list(reversed(cur.execute("SELECT date, status FROM messages WHERE user_id=(?)",
                                         (message.chat.id,)).fetchall()))
    all_msgs.sort(key=lambda x: x[1])

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    btns_closed = [telebot.types.InlineKeyboardButton(text=f"{statuses[x[1]]} {x[0]} ", callback_data=f"get_msg_{x[0]}")
                   for x in all_msgs]
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_help')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(*btns_closed)
    markup.add(menu_button)
    markup.add(student_menu_button)

    bot.send_message(message.chat.id, "⚠️ - Вопрос открыт\n"
                                      "✅ - Вопрос закрыт\n\n"
                                      "Выберите время отправки вопроса:", reply_markup=markup, parse_mode='html')


@bot.callback_query_handler(func=lambda call: 'get_msg_' in call.data)  # получение текста выбранного вопроса
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
    plus_quest = telebot.types.InlineKeyboardButton("Дополнить вопрос", callback_data='send_question')
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='memory')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    close_button = telebot.types.InlineKeyboardButton("Вопрос решен", callback_data=f'close_msg_s_{total_msg[3]}')
    markup.add(plus_quest, close_button, menu_button, student_menu_button) if total_msg[2] == 1 \
        else markup.add(menu_button, student_menu_button)

    for msg in telebot.util.smart_split(msg_text, 3000):
        if msg != telebot.util.smart_split(msg_text, 3000)[-1]:
            bot.send_message(message.chat.id, msg_text, parse_mode='html')
        else:
            bot.send_message(message.chat.id, msg_text, parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: 'close_msg_' in call.data)  # закрытие вопроса сотрудником или студентом
def close_question(call):
    message = call.message

    role, talk_id = call.data.split('_')[2:]
    cur.execute("""UPDATE messages SET status=(?) WHERE talk_id=(?)""", (2, talk_id))
    con.commit()

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    if role == 's':
        menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='memory')
    else:
        student_user_id = int(
            cur.execute("""SELECT user_id FROM messages WHERE talk_id=(?)""", (talk_id,)).fetchone()[0])
        bot.send_message(student_user_id, 'Ваш вопрос был закрыт сотрудником.')
        menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='help_student')
    markup.add(menu_button)

    bot.send_message(message.chat.id, "Вопрос успешно закрыт!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'clean_memory')  # очистка архива студента
def clean_memory(call):
    message = call.message

    cur.execute("""DELETE FROM messages WHERE user_id=(?)""", (message.chat.id,))
    con.commit()

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    student_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='get_help')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='student_menu')
    markup.add(menu_button)
    markup.add(student_menu_button)

    bot.send_message(message.chat.id, "Архив успешно очищен!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'employee_menu')  # меню сотрудника
def employee_menu(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    clear_button = telebot.types.InlineKeyboardButton("🗑 Забыть меня", callback_data="clear_prof")
    global_button = telebot.types.InlineKeyboardButton("📢 Отправить глобальное сообщение", callback_data="global_send")
    helpst_button = telebot.types.InlineKeyboardButton("❔ Вопросы студентов", callback_data="help_student")
    students_menu = telebot.types.InlineKeyboardButton("📚 Меню для студентов", callback_data="student_menu")
    markup.add(global_button, students_menu, helpst_button, clear_button)

    bot.send_message(message.chat.id, f"Сотрудник, вам доступны следующие функции:",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'global_send')  # глобальное сообщение студентам
def global_send(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    cancel_button = telebot.types.InlineKeyboardButton("Отменить отправку", callback_data='cancel_send_e')
    markup.add(cancel_button)

    bot.send_message(message.chat.id, "Напишите глобальное сообщение, "
                                      "оно будет отправлено через бота всем студентам. Если нужно прикрепить файл, "
                                      "загрузите его в облако и оставьте в сообщении ссылку\n\n"
                                      "Можно использовать html теги для текста. Например:\n"
                                      "<b>текст</b> - жирный текст\n"
                                      "<i>текст</i> - курсив\n"
                                      "<u>текст</u> - подчеркнутый",
                     reply_markup=markup)

    bot.register_next_step_handler_by_chat_id(message.chat.id, send_global_msg)


def send_global_msg(message):  # функция отправки глобального сообщения
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    employee_menu_button = telebot.types.InlineKeyboardButton("💠Меню", callback_data='employee_menu')
    markup.add(employee_menu_button)

    shadow_markup = telebot.types.InlineKeyboardMarkup(row_width=1)  # markup for students
    student_menu_button = telebot.types.InlineKeyboardButton("💠Меню", callback_data='student_menu')
    shadow_markup.add(student_menu_button)

    ids = cur.execute("""SELECT id FROM profiles WHERE
                      role=(SELECT number FROM roles WHERE name='student')""").fetchall()[0]
    textlist = telebot.util.smart_split(message.text, 3000)
    for id_students in ids:
        for count, msg in enumerate(textlist):
            if count == 0:
                bot.send_message(id_students, f"<b><i>❗Глобальное сообщение от сотрудника:</i></b>\n\n{msg}",
                                 parse_mode='html', reply_markup=shadow_markup if len(textlist) <= 1 else None)
            else:
                bot.send_message(id_students, f"{msg}",
                                 parse_mode='html', reply_markup=shadow_markup)
    bot.send_message(message.chat.id, f"Сообщение успешно отправлено!",
                     parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'help_student')  # вопросы от студентов
def questions_menu(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    button_texts = ['⚠️ Открытые', '✅ Закрытые', 'Все']

    for i, text in enumerate(button_texts):
        button_texts[i] = telebot.types.InlineKeyboardButton(text, callback_data=f"get_questions {i + 1}")
    employee_menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='employee_menu')

    markup.add(*button_texts)
    markup.add(employee_menu_button)

    bot.send_message(message.chat.id, f"Выберите раздел вопросов:",
                     parse_mode='html', reply_markup=markup)


# получение сотрудником списка вопросов выбранного раздела (открытые, закрытые, все)
@bot.callback_query_handler(func=lambda call: 'get_questions' in call.data)
def get_questions(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    queries_posts = {'1': ("""SELECT user_id, date FROM messages WHERE status=1""", '⚠️ ', "opened"),
                     '2': ("""SELECT user_id, date FROM messages WHERE status=2""", '✅ ', "closed")}
    if '1' in call.data[-1] or '2' in call.data[-1]:
        questions_ids = cur.execute(queries_posts[call.data[-1]][0]).fetchall()
        buttons = [
            telebot.types.InlineKeyboardButton(f"{queries_posts[call.data[-1]][1]}{x[1]}",
                                               callback_data=f"getqsts_{queries_posts[call.data[-1]][2]}_{x[0]}_{x[1]}")
            for x in questions_ids
        ]
        if '2' in call.data[-1]:
            buttons.append(telebot.types.InlineKeyboardButton(f"Удалить закрытые вопросы",
                                                              callback_data='delete_closed_'))
    else:
        questions_ids = list(reversed(cur.execute("""SELECT user_id, date, status FROM messages""").fetchall()))
        questions_ids.sort(key=lambda x: x[2])
        buttons = [
            telebot.types.InlineKeyboardButton(f"{'⚠️ ' if x[2] == 1 else '✅ '}{x[1]}",
                                               callback_data=f"getqsts_all_{x[0]}_{x[1]}") for x in questions_ids
        ]
    markup.add(*buttons)
    employee_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='help_student')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='employee_menu')
    markup.add(menu_button)
    markup.add(employee_menu_button)

    bot.send_message(message.chat.id, f"Выберите интересующий вопрос:",
                     parse_mode='html', reply_markup=markup)


# получение текста выбранного вопроса с соответствующим функционалом и визуальным оформлением
@bot.callback_query_handler(func=lambda call: 'getqsts_' in call.data)
def get_current_question(call):
    message = call.message
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    status, user_id, date = call.data.split('_')[1:]
    total_msg = cur.execute(
        """SELECT from_user, to_user, status, talk_id FROM messages WHERE user_id=(?) AND date=(?)""",
        (int(user_id), date)).fetchone()  # вопрос студента, ответ сотрудника, статус вопроса, уникальный id
    user_msg = total_msg[0].split(splitter)  # вопрос студента разбитый по разделам
    answer_msg = total_msg[1].split(splitter) if total_msg[1] else []  # ответ сотрудника разбит соответствующе
    msg_text = f"Статус вопроса: {'Вопрос открыт' if total_msg[2] == 1 else 'Вопрос закрыт'}\n\n"  # шапка текста

    for i in range(len(user_msg)):  # заполнение текста всего вопроса
        msg_text += f'<b>Часть вопроса №{i + 1}.</b> {user_msg[i]}\n\n'
        if i < len(answer_msg):
            msg_text += f'<b>Ответ сотрудника: </b><i>{answer_msg[i]}</i>\n\n' \
                if answer_msg[i] else '<b>Ответ сотрудника: </b><i>Сотрудник еще не ответил.</i>'
    if len(answer_msg) > len(user_msg) and answer_msg[-1]:  # сотрудник написал ответ на вопрос несколько раз => UPD
        msg_text += "<i>UPD:</i> " + '\n'.join(answer_msg[len(user_msg):len(answer_msg)])

    if status == 'opened' or status == 'all' and int(total_msg[2]) == 1:  # кнопки функционала для открытого вопроса
        answer_action = telebot.types.InlineKeyboardButton("Ответить на вопрос",
                                                           callback_data=f"answer_on_{total_msg[3]}")
        close_action = telebot.types.InlineKeyboardButton("Закрыть вопрос",
                                                          callback_data=f"close_msg_e_{total_msg[3]}")
        markup.add(answer_action, close_action)

    elif status == 'closed':  # кнопки для закрытого вопроса
        delete_action = telebot.types.InlineKeyboardButton("Удалить выбранный вопрос",
                                                           callback_data=f"delete_closed_{date}")
        markup.add(delete_action)
    employee_menu_button = telebot.types.InlineKeyboardButton("Назад", callback_data='help_student')
    menu_button = telebot.types.InlineKeyboardButton("В меню", callback_data='employee_menu')
    markup.add(menu_button, employee_menu_button)

    # умный сплит если весь вопрос слишком большой для отображения в одном сообщении
    for msg in telebot.util.smart_split(msg_text, 3000):
        if msg != telebot.util.smart_split(msg_text, 3000)[-1]:
            bot.send_message(message.chat.id, msg_text, parse_mode='html')
        else:
            bot.send_message(message.chat.id, msg_text, parse_mode='html', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: 'answer_on_' in call.data)  # ответ сотрудника на выбранный вопрос
def answer_on(call):
    message = call.message
    bot.send_message(message.chat.id, "Отправьте ответ на вопрос в чат")
    bot.register_next_step_handler_by_chat_id(message.chat.id, save_answer, [call.data.split('_')[-1]])


def save_answer(message, chtid):  # функция сохранения ответа и уведомления студента
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    menu = telebot.types.InlineKeyboardButton("💠В меню", callback_data='employee_menu')
    markup.add(menu)

    shadow_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    archive = telebot.types.InlineKeyboardButton("Архив", callback_data='memory')
    shadow_markup.add(archive)

    talk_id = int(chtid[0])
    user_from, user_to, user_id, date = cur.execute("""SELECT from_user, to_user, user_id,
     date FROM messages WHERE talk_id=(?)""", (talk_id,)).fetchone()
    new_from = user_from + splitter
    new_to = user_to + message.text if user_to else message.text

    cur.execute("""UPDATE messages SET from_user=(?), to_user=(?) WHERE talk_id=(?)""",
                (new_from, new_to, talk_id))
    con.commit()

    to_question = telebot.types.InlineKeyboardButton("К вопросу", callback_data=f"get_msg_{date}")
    shadow_markup.add(to_question)

    bot.send_message(user_id, f"На ваш вопрос {date} ответил сотрудник. "
                              f"Проверьте архив и дополните через 'Задать вопрос' или закройте его.",
                     reply_markup=shadow_markup)
    bot.send_message(message.chat.id, "Ответ успешно отправлен!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: 'delete_closed' in call.data)  # удаление закрытых вопросов из БД
def delete_closed(call):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    menu = telebot.types.InlineKeyboardButton("💠В меню", callback_data='employee_menu')
    markup.add(menu)
    if not call.data.split("_")[-1]:
        cur.execute(
            """DELETE FROM messages WHERE status=(SELECT number FROM statuses WHERE status_name = 'Вопрос закрыт')""")
        con.commit()
        bot.send_message(call.message.chat.id, "Закрытые вопросы успешно удалены.", reply_markup=markup)
    else:
        date = call.data.split('_')[-1]
        cur.execute("""DELETE FROM messages WHERE status=(SELECT number FROM statuses WHERE status_name='Вопрос закрыт') 
        AND date=(?)""", (date,))
        con.commit()
        bot.send_message(call.message.chat.id, f"Закрытый вопрос {date} успешно удален.", reply_markup=markup)


bot.infinity_polling(skip_pending=True)  # бесконечная работа бота
# Максим Щилко 2024 https://vk.com/m.shilko
