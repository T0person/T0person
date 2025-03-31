from multiprocessing.spawn import prepare
import gradio as gr
import json
# import structlog
# import logging.config
# import structlog
import os
from TTS.api import TTS
import torch
import whisper
from Levenshtein import ratio
from pydub import AudioSegment
from get_jsoin_data import prepare_json_file

prepare_json_file()

temp_voice_dir = "./temp_voices"
voice_dir = "./voices"

device = "cuda" if torch.cuda.is_available() else "cpu"

# Открытие json
def open_json(name_file:str):
    with open(name_file, 'r+') as file:
        file_parse = json.load(file)
    return file_parse


def change_voice(_temp_path:str, _file_name:str, _type:str):
    _total_path = os.path.join(voice_dir,_file_name+".mp3")
    
    sound = AudioSegment.from_file(_temp_path)
    
    if _type=="Злой":
        
        octaves = -0.5

        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))

        sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        sound = sound.set_frame_rate(44100)
        # Скорость вопсроизведения звука
        velocidad_X = 1.2
        
        sound = sound.speedup(velocidad_X)
    elif _type=="Грустный":
        # Изменение тона
        octaves = 0.5

        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))

        sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        sound = sound.set_frame_rate(44100)
    else:
        _total_path = _temp_path
    
    sound.export(_total_path, format = 'mp3')    
    
    return _total_path

class Gradio_logic:
    def __init__(self):
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        self.recognite_model = whisper.load_model("large").to(device)
    
    def prepare_temp_audios(self):
        for quest, quest_value in DATA.items():
            quest_text = quest_value['text']
            
            # print(f"quest_name: {quest}")
            # print(f"quest_text: {quest_text}")
            
            self.use_tts(quest_text, quest)
        
    # Использование TTS
    def use_tts(self, text:str, name:str):
        path = f'{temp_voice_dir}/{name}.wav'
        if not os.path.exists(path):
            self.tts.tts_to_file(text=text, speaker="Viktor Menelaos", language="ru", file_path=path, )
        return path
    
    # Транскрибация
    def speech2text(self, speech:gr.Audio, message:str, chat_history:gr.Chatbot, _id_answer, _id_question):
        transcription = self.recognite_model.transcribe(speech, language='ru')
        
        chat_history.append({"role": "user", "content": message})
        
        audio_ratio = Gradio_logic.check_Levenshtein(transcription['text'], message)
        
        audio_answer = gr.Audio(None, interactive=False)
        answer = gr.Dropdown(interactive=True)
        
        # Добавить Логирование
        # logger.info(
        #     "Upload_message",
        #     answer=message,
        #     voice_answer=transcription,
        #     ratio=audio_ratio,
        #     outID=_id_answer,
        #     linkID=_id_question
        #     )
        # Через логер не получилось (Добавляются GET запросы)
        _data = {
            "event":"Upload_message",
            "answer":message,
            "voice_answer":transcription['text'],
            "ratio":audio_ratio,
            "outID":_id_answer,
            "linkID":_id_question
        }
        
        with open('log.json', 'a', encoding='utf-8') as file:
            json.dump(_data, file,ensure_ascii=False)
        
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
    @staticmethod
    def get_QA(_question="Вопрос 1"):
        _question_text = DATA[_question]['text']
        _answer =  _question.replace("Вопрос", "Ответ")
        _answers = []
        for ans_id in range(1,10):
            try:
                _answers.append(DATA[_question][f"{_answer}.{ans_id}"])
            except:
                break
            
            
        return _question_text, _answers

    # Логика получения вопросов и ответов
    @staticmethod
    def QA_logic(_actual_question):
        # Если первый вопрос
        if _actual_question == None:
            _question_text, _actual_answers = Gradio_logic.get_QA()
            audio_file_name = "Вопрос 1"

        else:
            for label_question, value in DATA.items():
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
        
        audio_file_path = change_voice(audio_file_path, audio_file_name, _emotion)
        
        
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

# Глобальная переменная вопросов и ответов
DATA = open_json("data.json")
emotion_list = ['Нейтральный', 'Злой', 'Грустный']

gradio_logic = Gradio_logic()

# logging.config.dictConfig({
#         "version": 1,
#         "disable_existing_loggers": True,
#         "handlers": {
#             "file": {
#                 "level": "INFO",
#                 "class": "logging.handlers.WatchedFileHandler",
#                 "filename": "log.json",
#             },
#         },
#         "loggers": {
#             "": {
#                 "handlers": ["file"],
#                 "level": "INFO",
#                 "propagate": True,
#             },
#         }
# })

# structlog.configure(
#     processors=[
#         structlog.processors.add_log_level,
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.EventRenamer("type"),
#         structlog.processors.JSONRenderer(),
#     ],
#     logger_factory=structlog.stdlib.LoggerFactory(),
#     wrapper_class=structlog.stdlib.BoundLogger,
#     cache_logger_on_first_use=True,
# )

# logger = structlog.get_logger()

with gr.Blocks() as demo:
    # Переменые сеанса
    id_actual_question = gr.State(None) # Первый вопрос или следующий
    id_answer = gr.State()
    id_fist_question = gr.State(None) # Первый вопрос (возврат)
    
    actual_answers = gr.State()


    with gr.Row():
        with gr.Column():
            emotion = gr.Dropdown(
                emotion_list,
                label="Эмоции",
                info="Выберите эмоции",
                interactive=True)
            # Ответы
            answer = gr.Dropdown(
                None,
                label="Ответы",
                info="Выберите ответ",
                interactive=True)
        
        # Запись аудио
        audio_answer = gr.Audio(sources="microphone", type="filepath", interactive=False)
        
    chatbot = gr.Chatbot(type="messages")
    
    # Аудио вопроса
    question_audio=gr.Audio(type="filepath", interactive=False, autoplay=True)
    

    # Выбор ответа
    answer.select(Gradio_logic.answer_select, [answer, actual_answers, id_fist_question], [answer, audio_answer, id_actual_question, id_answer])
    
    # Остановка записи и запуск чата
    audio_answer.stop_recording(gradio_logic.speech2text,
                                inputs=[audio_answer, answer, chatbot, id_answer, id_actual_question],
                                outputs=[chatbot, answer, audio_answer])\
                                    .then(gradio_logic.gr_logic_chat, [id_actual_question, emotion, chatbot], outputs=[chatbot, answer, actual_answers, question_audio])

    
    # При запуске app
    demo.load(gradio_logic.prepare_temp_audios)\
        .then(gradio_logic.gr_logic_chat, [id_actual_question, emotion, chatbot], outputs=[chatbot, answer, actual_answers, question_audio])
    # with gr.Column():
    #     with gr.Row():
    #         # Запись с микрофона
    #         # audio = 
            
    #         # Выбор эмоции
    #         emotion = gr.Dropdown(
    #             languages,
    #             label="Эмоции",
    #             info="Выберите эмоции",
    #             interactive=True)
    #         rs_hw = gr.Dropdown(choices=homeworks['english'], interactive=True)

    #     with gr.Row():
    #         question_audio = gr.Audio(label='Аудио от собеседника', interactive=False)
    #         b_ok = gr.Button(value="Продолжить", visible=True)
    #         b_cansel = gr.Button(value='Снова', visible=False)
    
    
    # audio.stop_recording(fn=gr_audio_stop_recording, inputs=[answer], outputs=[answer])
    # # emotion.change(gr_change_dropdown, inputs=[emotion], outputs=[rs_hw])
    # emotion.select(gr_emotion_select, inputs=[emotion], outputs=[label_answer])
            
        
demo.launch(debug=True)