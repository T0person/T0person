
from utils import read_json
import whisper
from TTS.api import TTS
import torch
import os
import gradio as gr
import logging
from utils import change_voice
from Levenshtein import ratio
from pythonjsonlogger.json import JsonFormatter

device = "cuda" if torch.cuda.is_available() else "cpu"

# Логгер
logger = logging.getLogger()

logHandler = logging.FileHandler('log.json')
formatter = JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

formatter = JsonFormatter("{event}{answer}{voice_answer}{ratio}{outID}{linkID}{emotion}", style="{")

class Gradio_logic:
    def __init__(self, temp_voice_dir, voice_dir, _final_json_file_name):
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        self.recognite_model = whisper.load_model("large").to(device)
        self.temp_voice_dir = temp_voice_dir
        self.voice_dir = voice_dir
        self.DATA = read_json(_final_json_file_name)
    
    def prepare_temp_audios(self):
        """
        Подготовка возможных вопросов
        """
        for quest, quest_value in self.DATA.items():
            quest_text = quest_value['text']
            
            self.use_tts(quest_text, quest)
        
    # Использование TTS
    def use_tts(self, text:str, name:str):
        """
        Использование TTS

        Args:
            text (str): Текст
            name (str): Название сырого аудиофайла

        Returns:
            _type_: Путь к сырому аудиофайлу
        """
        path = f'{self.temp_voice_dir}/{name}.wav'
        if not os.path.exists(path):
            self.tts.tts_to_file(text=text, speaker="Viktor Menelaos", language="ru", file_path=path, )
        return path
    
    # Транскрибация
    def speech2text(self, speech:gr.Audio, message:str, chat_history:gr.Chatbot, _id_answer:str, _id_question:str, _emotion:str):
        """
        Отправка ответа боту

        Args:
            speech (gr.Audio): Голос
            message (str): Текст голоса
            chat_history (gr.Chatbot): История чата
            _id_answer (str): ID ответа
            _id_question (str): ID следующего вопроса
            _emotion (str): Эмоция

        Returns:
            _type_: История чата, изменение ответа и звука
        """
        transcription = self.recognite_model.transcribe(speech, language='ru')
        
        chat_history.append({"role": "user", "content": message})
        
        audio_ratio = Gradio_logic.check_Levenshtein(transcription['text'], message)
        
        audio_answer = gr.Audio(None, interactive=False)
        answer = gr.Dropdown(interactive=True)
        
        
        logger.info(
            {
                "event":"Upload_message",
                "answer":message,
                "voice_answer":transcription['text'],
                "ratio":audio_ratio,
                "outID":_id_answer,
                "linkID":_id_question,
                "emotion": _emotion
                }
            )
        
        # _data = {
        #     "event":"Upload_message",
        #     "answer":message,
        #     "voice_answer":transcription['text'],
        #     "ratio":audio_ratio,
        #     "outID":_id_answer,
        #     "linkID":_id_question,
        #     "emotion": _emotion
        # }
        
        # with open('log.json', 'a', encoding='utf-8') as file:
        #     json.dump(_data, file,ensure_ascii=False)
        
        return chat_history, answer, audio_answer
    
    # Изменение интерфейса
    @staticmethod
    def answer_select(_answer:str, _actual_answers:dict, _id_fist_question):
        """
        Функция получения ID следующего вопроса

        Args:
            _answer (str): Текст выбранного ответа
            _actual_answers (dict): Доступные ответы

        Returns:
            _type_: Изменение интерфейса * 2, следующий вопрос
        """
        _id_next_question = False
        for i in _actual_answers:
            if i['text'] == _answer:
                _id_next_question =  i['linkID']
                _out_id = i["outID"]
                break
        if not _id_next_question:
            _id_next_question = _id_fist_question
            _out_id = None
        
        return gr.Dropdown(interactive=False), gr.Audio(interactive=True), _id_next_question, _out_id

    # Выборка вопросов и ответов
    def get_QA(self, _question="Вопрос 1"):
        """
        Выборка воросов на каждом шаге

        Args:
            _question (str, optional): Название вопросов. Defaults to "Вопрос 1".

        Returns:
            _type_: Текст вопроса и перечень ответов
        """
        _question_text = self.DATA[_question]['text']
        _answer =  _question.replace("Вопрос", "Ответ")
        _answers = []
        for ans_id in range(1,10):
            try:
                _answers.append(self.DATA[_question][f"{_answer}.{ans_id}"])
            except:
                break
            
            
        return _question_text, _answers

    # Логика получения вопросов и ответов
    def QA_logic(self, _actual_question):
        """
        Логика получения вопросов и ответов

        Args:
            _actual_question (_type_): Актуальные вопросы на шаге

        Returns:
            _type_: Вопрос, актуальные ответы и звук
        """
        # Если первый вопрос
        if _actual_question == None:
            _question_text, _actual_answers = Gradio_logic.get_QA()
            audio_file_name = "Вопрос 1"

        else:
            for label_question, value in self.DATA.items():
                if value.get("quest_id") == _actual_question:
                    audio_file_name = label_question
                    _question_text, _actual_answers = Gradio_logic.get_QA(label_question)
                    break
                    
        return _question_text, _actual_answers, audio_file_name

    def gr_logic_chat(self, _id_next_question, _emotion, chat_history:gr.Chatbot):
        """
        Функция логики отправки сообщения

        Args:
            _actual_question (None|id_next_question): ID следующего вопроса или None (Первый вопрос)
            chat_history (gr.Chatbot): Остеживание чата

        Returns:
            _type_: Чат, Dropdown меню, Список ответов
        """
        _question_text, _answers, audio_file_name = Gradio_logic.QA_logic(_id_next_question)
        _answers_text = [i['text'] for i in _answers]
        audio_file_path = self.use_tts(_question_text, audio_file_name)
        
        audio_file_path = change_voice(audio_file_path, audio_file_name, _emotion, self.voice_dir)
        
        
        # В Json файле была утеряна нить так что такой костыль
        if "Продолжаем?" in _answers_text:
            _answers_text.append("С начала?")
        
        _answer = gr.Dropdown(
                _answers_text,
                label="Ответы",
                info="Выберите ответ",
                interactive=True)
        
        chat_history.append({"role": "assistant", "content": _question_text})
        
        _audio = gr.Audio(audio_file_path, type="filepath", interactive=False, autoplay=True)
        
        return chat_history, _answer, _answers, _audio
    
    @staticmethod
    def check_Levenshtein(audio_text, text):
        try:
            similarity_score = ratio(audio_text, text)
        except:
            similarity_score = "Не было слышно (Не распознано)"
        return similarity_score