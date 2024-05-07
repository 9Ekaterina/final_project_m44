import requests
from config_m44 import FID, YATOKEN

# Выполняем запрос к YandexGPT
def ask_gpt_tts (prompt):
    headers = {
        'Authorization': f'Bearer {YATOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FID}/yandexgpt-lite",  # модель для генерации текста
        "completionOptions": {
            "stream": False,  # потоковая передача частично сгенерированного текста выключена
            "temperature": 0.6,  # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
            "maxTokens": "50"  # максимальное число сгенерированных токенов, очень важный параметр для экономии токенов
        },
        "messages": [
            {
                "role": "user",  # пользователь спрашивает у модели
                "text": prompt  # передаём текст, на который модель будет отвечать
            }
        ]
    }

    # Выполняем запрос к YandexGPT
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                             headers=headers,
                             json=data)

    # Проверяем, не произошла ли ошибка при запросе
    if response.status_code == 200:
                # достаём ответ YandexGPT
        text = response.json()["result"]["alternatives"][0]["message"]["text"]
        return text
    else:
        raise RuntimeError(
            'Invalid response received: code: {}, message: {}'.format(
                {response.status_code}, {response.text}
            )
        )
