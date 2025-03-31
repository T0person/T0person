import json
import re

# Запись в файл
def write_json(file_name:str, data:dict):
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)

with open('source.json', 'r+') as file:
    file_parse = json.load(file)
    
def prepare_json_file():
    
    
    num_pattenrn = re.compile(r"\d+?")
    question_pattern = re.compile(r"\d\..+")


    list_answers = []
    dict_questions = {}

    # Выборка вопросов и ответов
    for question_id, item in enumerate(file_parse):
        question = item['data']['content']
        connect_id = item['data']['connectId']
        
        dict_questions[question] = connect_id
        
        answers = item['data']['answer']
        
        for answer in answers:
            text = answer['content']
            id = answer['uuidlink']
            out_id = answer['uuidknot']
            
            
            temp = re.search(question_pattern, text)
            if temp == None:
                list_answers.append([text, id, out_id])
            else:
                dict_questions[text] = id
                list_answers.append(["Продолжаем?", id, out_id])
            

    dict_json = {}
    total_quest_id = 0

    # Состыковка вопросов и ответов
    for question_text, id in dict_questions.items():
        not_use = True
        answer_id = 1
        
        temp = re.search(question_pattern, question_text)
        question = question_text.replace(temp.group(), "")[2:]
        
        
        for answer in list_answers:
            answer_text = answer[0]
            answer_link_id = answer[1]
            answer_out_id = answer[2]
            
            if answer_out_id == id:
                not_use = False
                check_quest = dict_json.get(f"Вопрос {total_quest_id+1}")
                if check_quest == None:
                    dict_json[f"Вопрос {total_quest_id+1}"] = {
                        "text": question,
                        "quest_id": id,
                        f"Ответ {total_quest_id+1}.{answer_id}" : {
                            "text" : answer_text,
                            "linkID": answer_link_id,
                            "outID": answer_out_id
                            }
                        }
                else:
                    check_quest[f"Ответ {total_quest_id+1}.{answer_id}"] = {
                        "text" : answer_text,
                        "linkID": answer_link_id,
                        "outID": answer_out_id
                        }
                answer_id +=1
        
        # if not_use:
        #     dict_json[f"Вопрос {total_quest_id+1}"] = {
        #                         "text": question,
        #                         "quest_id": id}
        
        total_quest_id +=1



        
    write_json("data.json", dict_json)


    


    # 27 00:00-00:30
    # 27 18:40-01:00
    # 28 8:00-18:00