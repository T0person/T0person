import os
from docxtpl import DocxTemplate


class Docx:
    def __init__(self, type_org, list_data):
        self.type_org = type_org
        self.list_data = list_data
        self.template_data = {}
        self.TEMPLATES_PATH = r".\templates"
        self.DOCUMENTS_PATH = r".\documents"
        self.org_files = ["Журналы", "Инструкции", "Приказы", "Согласия"]

        for data in self.list_data:
            if data["val_post"] != "":
                self.template_data[data["var_post"]] = data["val_post"]
            if data["val_fio"] != "":
                self.template_data[data["var_fio"]] = data["val_fio"]

    def create_template(self, _path, _final_doc_path):
        doc = DocxTemplate(_path)
        doc.render(self.template_data)
        doc.save(_final_doc_path)

    def create_dirs(self, _path):
        try:
            os.makedirs(_path)
            print(f"Вложенные каталоги '{_path}' успешно созданы.")
        except FileExistsError:
            print(f"Один или несколько каталогов в «{_path}» уже существуют.")
        except PermissionError:
            print(f"Разрешение отклонено: невозможно создать '{_path}'.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def find_docx(self, _dir):
        org_path = os.path.join(self.TEMPLATES_PATH, self.type_org, _dir)
        final_org_path = os.path.join(self.DOCUMENTS_PATH, _dir)
        try:
            list_org_files = os.listdir(org_path)
        except Exception as e:
            print(e)

        for file_name in list_org_files:
            if "~" in file_name:
                continue
            elif '.docx' not in file_name:
                self.create_dirs(os.path.join(final_org_path, file_name))
                self.find_docx(os.path.join(_dir, file_name))
            else:
                total_doc_path = os.path.join(final_org_path, file_name)
                self.create_template(os.path.join(org_path, file_name), total_doc_path)
