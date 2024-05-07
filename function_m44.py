# импорт библиотек
import sqlite3
import requests
from datetime import datetime, date, time
from config_m44 import DATABASE, MAX_USERS, YATOKEN, MAX_MODEL_TOKENS, FID, MAX_TOKENS_IN_SESSION

print(datetime.now())

#Когда пользователь даёт команду /start проверяем и если нет, создаём базу
def sql_start(user_id_session):
    con = sqlite3.connect(DATABASE, check_same_thread=False)

    # Подключаем sqlite3.Row
    con.row_factory = sqlite3.Row


    # Создаём специальный объект cursor для работы с БД
    # Вся дальнейшая работа будет вестись через методы этого объекта: cur
    cur = con.cursor()

    # ЗДЕСЬ БУДЕТ ПРОИСХОДИТЬ САМА РАБОТА С БАЗОЙ: ОТПРАВКА ЗАПРОСОВ, ПОЛУЧЕНИЕ ОТВЕТОВ
    # Готовим SQL-запрос
    # Для читаемости запрос обрамлён в тройные кавычки и разбит построчно
    query = '''
    CREATE TABLE IF NOT EXISTS prompts(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        type_message_text TEXT,
        user_text TEXT,
        ya_text TEXT, 
        date DATATIME,
        tokens_tts INTEGER,
        audio_blocks INTEGER,
        symbol_stt INTEGER
        );
            '''
    cur.execute(query)
    con.commit()

def type (user_id_session):
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    query = f''' INSERT INTO prompts VALUES (NULL,{user_id_session},NULL,NULL,NULL,NULL,NULL,NULL)
                '''
    cur.execute(query)
    con.commit()
    con.close()

def sql_insert_data_prompts(user_id_session, type, user_text, ya_text, tokens_tts, audio_blocks, symbol_stt):
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    cur = con.cursor()
    now_data = datetime.now()
    query = f'''INSERT INTO prompts VALUES (NULL, {user_id_session}, "{type}", "{user_text}", "{ya_text}", "{now_data}", "{tokens_tts}", "{audio_blocks}", "{symbol_stt}")'''

    cur.execute(query)
    con.commit()
    con.close()

def count_tokens(text):
    headers = {
        'Authorization': f'Bearer {YATOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FID}/yandexgpt/latest",
        "maxTokens": MAX_MODEL_TOKENS,
        "text": text
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json=data,
            headers=headers
        ).json()['tokens']
    )  # здесь, после выполнения запроса, функция возвращает количество токенов в text

    # ОТЛАДКА: сколько токенов в запросе пользователя
    print(count_tokens("сюда будем передавать запрос пользователя"))



def read_tokens (user_id_session):
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    cur = con.cursor()

    query = f'''SELECT symbol_stt FROM prompts WHERE user_id = {user_id_session} ORDER BY date DESC LIMIT 1'''

    result = cur.execute(query).fetchone()
    result = result[0]
    con.close()
    return result



def count_tokens_ya (responseya):
    headers = {
        'Authorization': f'Bearer {YATOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FID}/yandexgpt/latest",
        "maxTokens": MAX_MODEL_TOKENS,
        "text": responseya
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json=data,
            headers=headers
        ).json()['tokens']
    )  # здесь, после выполнения запроса, функция возвращает количество токенов в text

    # ОТЛАДКА: сколько токенов в запросе пользователя
    print(count_tokens("сюда будем передавать запрос пользователя"))


#Функция: подсчёт количества пользователей
def is_limit_users():
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    cursor = con.cursor()
    result = cursor.execute('SELECT DISTINCT user_id FROM prompts')
    count = 0  # количество пользователей
    for i in result:  # считаем количество полученных строк
        count += 1  # одна строка == один пользователь
    con.close()
    return count > MAX_USERS

def is_limit_users_count():
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    cursor = con.cursor()
    result = cursor.execute('SELECT DISTINCT user_id FROM prompts').fetchall()
    #print("Вот сессия из базы:", result[1][0])
    count = 0  # количество пользователей
    for i in result:  # считаем количество полученных строк
        count += 1  # одна строка == один пользователь
    con.close()
    return count

def is_users_all():
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    cursor = con.cursor()
    result = cursor.execute('SELECT DISTINCT user_id FROM prompts').fetchall()
    return result

# функция подсчета токенов
def max_users_tocens(user_id_session):
    con = sqlite3.connect(DATABASE, check_same_thread=False)
    cursor = con.cursor()
    query = f"SELECT DISTINCT tokens_tts FROM  prompts where user_id = {user_id_session}  ORDER BY date DESC LIMIT 1"
    tokens = cursor.execute(query).fetchall()
    #ОТЛАДКА: печать максимального номера сессии пользователя
    print("Ответ от функции max_user_tocens : ",tokens[0][0])
    con.close()
    #tokens = tokens[0][0]
    if tokens == []:
        print("Результат пустой")
        tokens = 0
    else:
        tokens = tokens[0][0]

    return tokens