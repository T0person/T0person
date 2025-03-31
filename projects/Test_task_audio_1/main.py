import gradio as gr
from utils import read_initial_file, final_json_file_name
from interface import Gradio_logic

# Глобальная переменная вопросов и ответов
read_initial_file("./source.json")
emotion_list = ['Нейтральный', 'Злой', 'Грустный']
gradio_logic = Gradio_logic("./temp_voices", "./voices", final_json_file_name)


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
                                inputs=[audio_answer, answer, chatbot, id_answer, id_actual_question, emotion],
                                outputs=[chatbot, answer, audio_answer])\
                                    .then(gradio_logic.gr_logic_chat, [id_actual_question, emotion, chatbot], outputs=[chatbot, answer, actual_answers, question_audio])

    
    # При запуске app
    demo.load(gradio_logic.prepare_temp_audios)\
        .then(gradio_logic.gr_logic_chat, [id_actual_question, emotion, chatbot], outputs=[chatbot, answer, actual_answers, question_audio])
            
demo.launch(debug=True)