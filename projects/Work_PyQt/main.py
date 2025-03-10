from utils.logic import Docx
from utils.ui_data import left_ui_data, right_ui_data
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QButtonGroup, QRadioButton, QPushButton
from PyQt6.QtCore import Qt
import sys

class MainWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        self.type_org = ""
        self.initializeUI()
    
    # Инициализация базовой формы интерфейса
    def initializeUI(self):
        self.setGeometry(50, 100, 1400, 800) # Место и размеры окна
        self.setWindowTitle("Внесение информации")
        self.setMinimumSize(1200, 500)
        self.form()
        self.show()
    
    # Функция получения типа организации
    def get_radio_value(self, button):
        self.type_org = button.text()
        self.submit_button.setEnabled(True)
    
    def sumbit_click(self):
        _docx = Docx(self.type_org, self.total_data)
        _docx.find_docx("орг")
        _docx.find_docx("тех")
            
    def create_column(self, column_box, _data):
        for row in _data:
            # Определение элементов
            row_title = QLabel(row["title"], alignment=Qt.AlignmentFlag.AlignCenter)
            row_title.setStyleSheet("font: bold 14px;")
            row_title.setWordWrap(True)
            
            row_label_post = QLabel(row["label_post"], self)
            row_label_post.setWordWrap(True)
            
            row_input_post = QLineEdit("", self)
            
            row_label_fio = QLabel(row["label_fio"], self)
            row_label_fio.setWordWrap(True)
            
            row_input_fio = QLineEdit("", self)

            row_title.setMinimumWidth(200)
            row_label_post.setMinimumWidth(50)
            row_input_post.setMinimumWidth(200)
            row_label_fio.setMinimumWidth(50)
            row_input_fio.setMinimumWidth(200)
            
            # Мини вертикаль
            row_v_box = QVBoxLayout()
            row_v_box.addWidget(row_title)
            
            # Горизонталь
            row_h_box = QHBoxLayout()
            row_h_box.addWidget(row_label_post)
            row_h_box.addWidget(row_input_post)
            row_h_box.addWidget(row_label_fio)
            row_h_box.addWidget(row_input_fio)

            row_v_box.addLayout(row_h_box) # Добавление в мини-вертикаль
            
            column_box.addLayout(row_v_box)
            self.total_data.append(
                {
                    "var_post": row["value_post"],
                    "val_post": row_input_post.text(),
                    "var_fio": row["value_fio"],
                    "val_fio": row_input_fio.text(),
                },
            )
        return column_box
        
    
    def form(self):
        self.total_data = []
        
        main_box = QHBoxLayout() # Горизонтально
        
        # Лувый вертикальный столбец
        left_main_box = QVBoxLayout()
        row_v_box = QVBoxLayout() # Столбец внутри
        
        # Заполняем заголовок левого столбца
        row_title = QLabel("Тип организации:", alignment=Qt.AlignmentFlag.AlignCenter)
        row_title.setStyleSheet("font: bold 14px;")
        row_v_box.addWidget(row_title)
        
        # В левом столбце добавляем горизонталь
        row_h_box = QHBoxLayout()
        # row_h_box.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBaseline)

        # Создаем радио-кнопки
        radio_group = QButtonGroup(self)

        type_organization = ["Учреждение", "Общество", "Министерство"]
        for org in type_organization:
            radio_button = QRadioButton(org)
            radio_group.addButton(radio_button)
            row_h_box.addWidget(radio_button)
        radio_group.buttonClicked.connect(self.get_radio_value)
        # self.total_data.append(self.org)

        
        # Добавляем все в обратном порядке
        row_v_box.addLayout(row_h_box) # Добавление в мини вертикаль горизонталь
        left_main_box.addLayout(row_v_box) # Добавление всего вертикального столбца
        left_main_box = self.create_column(left_main_box,left_ui_data)

        main_box.addLayout(left_main_box) # Добавление левого столбца
        
        right_main_box = QVBoxLayout()
        right_main_box = self.create_column(right_main_box, right_ui_data)

        row_h_box = QHBoxLayout()
        self.submit_button = QPushButton("Запуск", self)
        self.submit_button.setEnabled(False)
        self.submit_button.clicked.connect(self.sumbit_click)
        self.submit_button.setFixedWidth(200)
        
        row_h_box.addWidget(self.submit_button)
        row_h_box.setAlignment(self.submit_button, Qt.AlignmentFlag.AlignHCenter)
        right_main_box.addLayout(row_h_box)
        main_box.addLayout(right_main_box) # Добавление левого столбца
        main_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        
        self.setLayout(main_box) # Объявление главной формы
        
        


if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    window = MainWindow()
    # Run the main Qt loop
    sys.exit(app.exec())