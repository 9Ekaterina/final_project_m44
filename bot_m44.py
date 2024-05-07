import telebot
from config_m44 import TOKEN, MAX_SYMBOL, MAX_PROJECT_TOKENS, MAX_MODEL_TOKENS
import math
import speech
import yandex
import function_m44
import ya_tts


# токен
bot = telebot.TeleBot(TOKEN)

# параметры для проверки на водд пользователя
CONTENT_TYPES = ["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact",
                 "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
                 "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
                 "migrate_from_chat_id", "pinned_message"]



@bot.message_handler(commands=['start'])
def start_user(message):
    button_1 = telebot.types.KeyboardButton("/begin")
    bot.send_message(message.chat.id, text=f"Привет, {message.from_user.first_name}, я бот-котик\n"
                                           "Отвечу на любой твои вопрос\n"
                                           "Чтобы начать жми -> /begin\n", reply_markup=telebot.types.ReplyKeyboardMarkup().add(button_1))
    function_m44.sql_start(message.from_user.id)
    if function_m44.is_limit_users() is True:
        bot.send_message(message.chat.id, "Прости, слишком много пользователей. Пока могу быть только ботом-попугаем")

        @bot.message_handler(content_types=['text'])
        def repeat_message(message):  # Функция для обработки сообщений
            bot.send_message(message.chat.id,
                             f"я бот-попугай потому что слишком много пользователей: {message.text}")  # Отправка ответ

        # Иначе если пользователь может пользоваться то мы начинаем работу с ботом
    elif function_m44.is_limit_users() is not True:
        bot.send_message(message.chat.id, "Продолжаем работу")
        # Считаем, сколько всего токенов у всех пользователей в проекте на данный момент
        total_count_users = function_m44.is_limit_users_count()
        print("Всего уникальных пользователей: ", total_count_users)
        i = 0
        total_bot_tokens = 0
        for user_id in function_m44.is_users_all():
            total_bot_tokens = total_bot_tokens + function_m44.max_users_tocens(user_id[i])
            print("Токены: ", total_bot_tokens)

        # проверяем бюджет токенов на весь проект
        if total_bot_tokens >= MAX_PROJECT_TOKENS:
            print("Прости, но токены в проекте вышли за рамки")
            bot.send_message(message.chat_id, "Прости но токены в проекте вышли за рамки")
        else:
            # считаем токены
            tokens = function_m44.max_users_tocens(message.from_user.id)
            if tokens > MAX_MODEL_TOKENS:
                bot.send_message(message.chat.id, "Вы превысили количесво токенов")
            else:
                tokens_spend = MAX_MODEL_TOKENS - tokens

                @bot.message_handler(commands=['begin'])
                def begin (message):
                    button_2 = telebot.types.KeyboardButton("/stt")
                    button_3 = telebot.types.KeyboardButton("/tts")
                    bot.send_message(message.chat.id, text=f"Давай начнем с того что, ты должен выбрать:\n"
                                                           f"Если хочешь отправить соообщение гололсом то пиши -> /stt\n"
                                                           f"Если хочешь отправить текстовое сообщение то пиши -> /tts\n", reply_markup=telebot.types.ReplyKeyboardMarkup().add(button_2, button_3))

                    function_m44.sql_insert_data_prompts(message.from_user.id, f"stt", "", "", "", "", "")

                @bot.message_handler(commands=['tts'])
                def tts(message):
                    global command_type
                    command_type = 'tts'
                    bot.send_message(message.chat.id, "Ты решил печатать свои вопрос. Я жду")

                    @bot.message_handler(commands=['solve_task_tts'])
                    def solve_task(message):
                        prompt = f"Найди ответ на вопрос: {user_text}"
                        responseya_tts = ya_tts.ask_gpt_tts(prompt)
                        print(responseya_tts)
                        text_symbols = len(responseya_tts)


                        tokens_ya_user = function_m44.read_tokens(message.from_user.id) + function_m44.count_tokens_ya(
                            responseya_tts)

                        function_m44.sql_insert_data_prompts(message.from_user.id, f"stt", f"{user_text}",f"{responseya_tts}", f"{tokens_ya_user}", "",  f"")

                        bot.send_message(message.chat.id, responseya_tts)

                    @bot.message_handler(content_types=CONTENT_TYPES)
                    def mess_engine(message):
                        global command_type, user_text

                        if message.content_type != ("text"):
                            bot.send_message(message.chat.id, "Необходимо отправить именно текстовое сообщение")
                            bot.send_message(message.chat.id,
                                             f"Мы остановились на команде /{command_type}. Если решишь продолжжить, просто нажми на команду!")
                            return mess_engine
                        else:
                            if command_type == ("tts"):
                                user_text = message.text
                                bot.send_message(message.chat.id, f"Ты ввел: {user_text}")
                                bot.send_message(message.chat.id, "Если хочешь получить ответ то жми -> /solve_task_tts")

                @bot.message_handler(commands=['stt'])
                def stt_handler(message):
                    global command_type, text_stt
                    command_type = "stt"
                    user_id = message.from_user.id
                    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
                    bot.register_next_step_handler(message, stt)
                    function_m44.sql_insert_data_prompts(message.from_user.id, f"stt", "", "", "", "", "")

                # Переводим голосовое сообщение в текст после команды stt
                def stt(message):
                    user_id = message.from_user.id

                    # Проверка, что сообщение действительно голосовое
                    if not message.voice:
                        return

                    file_id = message.voice.file_id  # получаем id голосового сообщения
                    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
                    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение

                    def is_stt_block_limit(message):
                        global audio_blocks
                        user_id = message.from_user.id

                        # Переводим секунды в аудиоблоки
                        audio_blocks = math.ceil(message.voice.duration / 15)  # округляем в большую сторону
                        print(audio_blocks)

                        # Проверяем, что аудио длится меньше 30 секунд
                        if message.voice.duration >= 30:
                            msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
                            bot.send_message(user_id, msg)
                            return None

                    bot.send_message(message.chat.id, "Ушел писать текст... ")




                    # Получаем статус и содержимое ответа от SpeechKit
                    status,  text_stt = speech.speech_to_text(file)  # преобразовываем голосовое сообщение в текст
                    is_stt_block_limit(message)
                    tokens = function_m44.count_tokens(text_stt)
                    print(tokens)
                    #function_m44.sql_insert_data_prompts(message.from_user.id, f"stt", f"{text}", "", f"", f"{tokens}")


                    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
                    if status == True:
                        print(text_stt)
                        function_m44.sql_insert_data_prompts(message.from_user.id, f"stt", f"{text_stt}", "", f"{tokens}", f"{audio_blocks}", "")


                        bot.send_message(user_id, text_stt, reply_to_message_id=message.id)
                        bot.send_message(message.chat.id, "Вот что ты сказал, если все так то жми -> /solve_task")

                    @bot.message_handler(commands=['solve_task'])
                    def solve_task(message):
                        prompt = f"Найди ответ на вопрос: {text_stt}"
                        responseya_stt = yandex.ask_gpt(prompt)
                        print(responseya_stt)
                        text_symbols = len(responseya_stt)


                        tokens_ya_user = function_m44.read_tokens(message.from_user.id) + function_m44.count_tokens_ya(responseya_stt)

                        function_m44.sql_insert_data_prompts(message.from_user.id, f"stt", f"{text_stt}", f"{responseya_stt}", f"{tokens_ya_user}",
                                                             f"", "")

                        if text_symbols > 1000:
                            bot.send_message(message.chat.id, "Прости это слишком длинное сообщение запиши его покороче")


                        else:

                            bot.send_message(message.chat.id, "Сообщение не привышает количество символов!")
                            bot.send_message(message.chat.id, "Ушел записывать звук... ")
                            yandex.text_to_speech(responseya_stt)
                            # Вызываем функцию и получаем результат
                            success, response = yandex.text_to_speech(responseya_stt)

                            if success:
                                # Если все хорошо, сохраняем аудио в файл
                                with open("output.ogg", "wb") as audio_file:
                                    audio_file.write(response)
                                print("Аудиофайл успешно сохранен как output.ogg")
                                user_id = message.from_user.id
                                audio = open(r'output.ogg', 'rb')
                                bot.send_audio(message.chat.id, audio)
                                audio.close()
                                bot.send_message(message.chat.id, "Если захочешь еще раз задать вопрос то жми -> /begin")

                            else:
                                # Если возникла ошибка, выводим сообщение об ошибке
                                print("Ошибка:", response)








bot.polling()