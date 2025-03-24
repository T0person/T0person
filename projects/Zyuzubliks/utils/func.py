import pandas as pd
import re
import bs4
from bs4 import BeautifulSoup
import requests
import os
from database import DB
import statistics

def prepare_data(targets:str) -> list:
    """
    Подготовка данных из файла для дальнейшей работы

    Args:
        targets (str): Строчка с путями из Excel

    Returns:
        list: Цели парсинга
    """
    
    targets = targets.split()
    total_targets = []
    for target in targets:
        _text = target.split("/")
        for i in _text:
            try:
                object = re.search(r".+\[", i).group()[:-1] # Div не div
                _type = re.search(r"\[.+\]", i).group()[1:-1] # class/id
                _type, path = _type.split("=") # название class/id
                total_targets.append([object,_type,path])
            except:
                total_targets.append([i])
        
    return total_targets

def read_data(url:bs4.element.Tag, path:list, total_url:bs4.element.Tag, ret_list=[]):
    """
    Рекусивный проход по элементам

    Args:
        url (bs4.element.Tag): Сайт
        path (list): Путю до элемента
        total_url (bs4.element.Tag): Базовый URL
        ret_list (list, optional): Переменная в функции (Возврат скрапинга). Defaults to [].

    Returns:
        ret_list(list): Рекурсия | итоговый список парсинга
    """
    # Возврат списка текста, если дальнейших путей нет
    if len(path) == 0:
        _text = url.get_text().strip()
        ret_list.append(_text)
        
        return ret_list
    
    temp_path = path[0] # Настоящий путь на данный момент
    
    # Если class | id
    if len(temp_path) > 1:
        temp = url.find(temp_path[0], {temp_path[1]: temp_path[2]}) # Поиска элемента
        
        path.pop(0) # Следующий шаг
        return read_data(temp, path, total_url)
    
    # Если тэг без class | id
    else:
        _text = url.find(temp_path[0]).get_text().strip() # Получаем элемент
        
        ret_list.append(_text) # Получаем текст тэга
        path.pop(0) # Следующий шаг
        return read_data(total_url, path, total_url)

def parse_data(url:str, targets:str, store:str, id = 0):
    """
    Основная функция парсинга

    Args:
        url (str): Сайт
        targets (str): Путь
        store (str): Название магазина
        id (int, optional): Переменная для подсчета целей. Defaults to 0.

    Returns:
        targets(list): Списко текста
        avg_price: Средняя цена по магазину
    """
    # Подготовка
    targets = prepare_data(targets)
    
    page = requests.get(url) # Получаем HTML
    print(f"Status code: {page.status_code}") # Проверяем статус
    
    soup = BeautifulSoup(page.content, "html.parser") # Парсим
    
    products = soup.find_all(targets[0][0], {targets[0][1]:targets[0][2]}) # Ищем div
        
    targets.pop(0) # Убираем начальный шаг
    
    # Выборка Названия и Цены
    for prod in products:
        total_list = read_data(prod, targets.copy(), prod)
    targets = []
    avg_price = []
    for i in range(0, len(total_list),2):
        text = total_list[i]
        j = i+1
        price = total_list[j]
        price = re.search(r"(?:\d+\s\d+|\d+)", price).group()
        price = int(re.sub(" ", "", price))
        targets.append((id, store, text, price))
        avg_price.append(price)
        id +=1
        
    avg_price = statistics.mean(avg_price)
    return targets, avg_price

async def read_excel(path: os.path, db:DB) -> None:
    """
    Функция чтения Excel

    Args:
        path (os.path): Путь к файлу

    Returns:
        str: Содержимое файла
    """
    rows_db = []
    df = pd.read_excel(path, header=None, names=["title", 'url', 'xpath'])
    answer_avg_price=[]
    for row in df.itertuples():
        
        rows_db.append((row.title, row.url, row.xpath))
        
        row_parse_db, avg_price = parse_data(row.url, row.xpath, row.title)
        
        answer_avg_price.append([row.title, avg_price])
        await db.update_parser_data(row_parse_db) # Обновление данных о товарах
        
    await db.update_file_data(rows_db) # Обновление данных по файлам
    return answer_avg_price