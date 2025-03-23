import asyncio
import aiohttp
import pandas as pd
from typing import List, Dict
import config

OPENWEATHER_API_KEY = config.openweather_key
NEWS_API_KEY = config.news_key
CITIES = ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Nizhny Novgorod",
          "Kazan", "Chelyabinsk", "Omsk", "Samara", "Rostov-on-Don", "Ufa", "Krasnoyarsk",
          "Voronezh", "Perm", "Krasnodar", "Saratov", "Tyumen", "Tolyatti", "Izhevsk",
          "Barnaul", "Ulyanovsk", "Irkutsk", "Kemerovo", "Vladivostok", "Makhachkala",
          "Arkhangelsk", "Vologda", "Kaliningrad", "Penza", "Lipetsk", "Tver"]


async def fetch_weather_data(session: aiohttp.ClientSession, city: str) -> Dict:
    """Асинхронная функция для получения данных о погоде"""

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"

    async with session.get(url) as response:
        return await response.json()


async def fetch_news_data(session: aiohttp.ClientSession) -> Dict:
    """Асинхронная функция для получения новостей о PC gaming"""

    url = f"https://newsapi.org/v2/everything?q=PC gaming&apiKey={NEWS_API_KEY}"

    async with session.get(url) as response:
        return await response.json()


async def fetch_random_users(session: aiohttp.ClientSession, count: int = 10) -> Dict:
    """Асинхронная функция для получения случайных пользователей"""

    url = f"https://randomuser.me/api/?nat=RU&results={count}"

    async with session.get(url) as response:
        return await response.json()


async def fetch_all_data():
    """ Главная асинхронная функция для сбора всех данных"""

    async with aiohttp.ClientSession() as session:
        # Параллельный сбор данных о погоде
        weather_tasks = [fetch_weather_data(session, city) for city in CITIES]
        weather_data = await asyncio.gather(*weather_tasks)

        # Параллельное получение новостей и пользователей
        news_task = fetch_news_data(session)
        users_task = fetch_random_users(session)
        news_data, users_data = await asyncio.gather(news_task, users_task)

        return weather_data, news_data, users_data


def save_to_excel(weather_data: List[Dict], news_data: Dict, users_data: Dict):
    """ Функция для сохранения данных в отдельные Excel файлы """

    # Сохраняем данные о погоде
    weather_df = pd.DataFrame([
        {
            'Город': data['name'],
            'Температура': data['main']['temp'],
            'Описание': data['weather'][0]['description']
        } for data in weather_data
    ])

    # Сохраняем данные о погоде в отдельный файл
    with pd.ExcelWriter('weather_api.xlsx', engine='openpyxl') as writer:
        weather_df.to_excel(writer, sheet_name='Погода', index=False)

    # Сохраняем новости в отдельный файл
    news_df = pd.DataFrame(news_data['articles'])
    with pd.ExcelWriter('news_api.xlsx', engine='openpyxl') as writer:
        news_df.to_excel(writer, sheet_name='Новости', index=False)

    # Сохраняем данные пользователей в отдельный файл
    users_df = pd.DataFrame(users_data['results'])
    with pd.ExcelWriter('users_api.xlsx', engine='openpyxl') as writer:
        users_df.to_excel(writer, sheet_name='Пользователи', index=False)

async def main():
    try:
        weather_data, news_data, users_data = await fetch_all_data()
        save_to_excel(weather_data, news_data, users_data)
        print("Данные успешно собраны и сохранены")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())