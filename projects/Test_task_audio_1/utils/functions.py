import json
import re
import os
from pydub import AudioSegment

final_json_file_name = "./data.json"
# Открытие json
def read_json(_path:str):
    """
    Чтение в Json

    Args:
        _path (str): Путь
    """
    kek = os.path.abspath(_path)
    with open(_path, 'r+') as file:
        file_parse = json.load(file)
    return file_parse


# Запись в файл
def write_json(_path:str, data:dict):
    """
    Запись в Json

    Args:
        _path (str): Путь
        data (dict): Информация
    """
    with open(_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)

def get_qa(_initial_file, _question_pattern):
    """
    Чтенеи вопросов и ответов из конечного файла

    Args:
        _initial_file (_type_): Исходный файл
        _question_pattern (_type_): Регулярка

    Returns:
        _type_: Список вопросов и ответов
    """
    _list_answers = []
    _dict_questions = {}

    # Выборка вопросов и ответов
    for item in _initial_file:
        question = item['data']['content']
        connect_id = item['data']['connectId']
        
        _dict_questions[question] = connect_id
        
        answers = item['data']['answer']
        
        for answer in answers:
            text = answer['content']
            id = answer['uuidlink']
            out_id = answer['uuidknot']
            
            
            temp = re.search(_question_pattern, text)
            if temp == None:
                _list_answers.append([text, id, out_id])
            else:
                _dict_questions[text] = id
                _list_answers.append(["Продолжаем?", id, out_id])
    return _list_answers, _dict_questions

def sample_json_file(_dict_questions:dict, _list_answers:list, _question_pattern):
    """
    Выборка вопросов и ответов

    Args:
        _dict_questions (dict): Перечень вопросов
        _list_answers (list): Перечень ответов
        _question_pattern (_type_): Регулярка

    Returns:
        _type_: Информация в Json
    """
    _dict_json = {}
    
    _total_quest_id = 1
    # Состыковка вопросов и ответов
    for question_text, id in _dict_questions.items():
        answer_id = 1
        
        temp = re.search(_question_pattern, question_text)
        question = question_text.replace(temp.group(), "")[2:]
        
        
        for answer in _list_answers:
            answer_text = answer[0]
            answer_link_id = answer[1]
            answer_out_id = answer[2]
            
            if answer_out_id == id:
                check_quest = _dict_json.get(f"Вопрос {_total_quest_id}")
                if check_quest == None:
                    _dict_json[f"Вопрос {_total_quest_id}"] = {
                        "text": question,
                        "quest_id": id,
                        f"Ответ {_total_quest_id}.{answer_id}" : {
                            "text" : answer_text,
                            "linkID": answer_link_id,
                            "outID": answer_out_id
                            }
                        }
                else:
                    check_quest[f"Ответ {_total_quest_id}.{answer_id}"] = {
                        "text" : answer_text,
                        "linkID": answer_link_id,
                        "outID": answer_out_id
                        }
                answer_id +=1
        
        _total_quest_id +=1
    return _dict_json


def read_initial_file(_path:str):
    """
    Чтение исходного файла

    Args:
        _path (str): Путь до файла
    """
    
    file_parse = read_json(_path)
    
    # Регулярное выражения для поиска вопроса
    question_pattern = re.compile(r"\d\..+")

    # Чтение исходного Json файла
    list_answers, dict_questions = get_qa( file_parse, question_pattern)

    # Выборка вопросов и ответов
    dict_json = sample_json_file(dict_questions, list_answers, question_pattern)

    # Запись в Json
    write_json(final_json_file_name, dict_json)
    

def add_effect(_octaves:float):
    """
    Добавление эффектов

    Args:
        _octaves (float): Изменения актавы

    Returns:
        _type_: Звук
    """
    
    new_sample_rate = int(sound.frame_rate * (2.0 ** _octaves))

    sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    sound = sound.set_frame_rate(44100)
    return sound
    

def change_voice(_temp_path:str, _file_name:str, _emotion:str, _voice_dir:str):
    """
    Изменение голоса

    Args:
        _temp_path (str): Пусть до .wav
        _file_name (str): Название файла без расширения
        _emotion (str): Эмоция
        _voice_dir (str): Папка для сохранения mp3

    Returns:
        _emotion_: путь до конечного файла
    """
    _total_path = os.path.join(_voice_dir,_file_name + ".mp3")
    
    sound = AudioSegment.from_file(_temp_path)
    
    if _emotion=="Злой":
        
        # Изменение тона
        sound = add_effect(-0.5)
        
        # Скорость вопсроизведения звука
        velocidad_X = 1.2
        
        sound = sound.speedup(velocidad_X)
    elif _emotion=="Грустный":
        
        # Изменение тона
        sound = add_effect(0.5)
    else:
        _total_path = _temp_path
    
    sound.export(_total_path, format = 'mp3')    
    
    return _total_path
