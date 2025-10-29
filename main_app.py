import sys
from PyQt6.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QPushButton, QStackedWidget, QSizePolicy 
)
from PyQt6.QtCore import Qt

# Импортируем все ваши модули
from db_connector import DBConnector
from gui.products_tab import ProductsWidget
from gui.storage_tab import StorageWidget
from gui.expenses_tab import ExpensesWidget
from gui.main_tab import MainWidget
from model import model

# НОВЫЙ ГЛУБОКИЙ ЯНТАРНЫЙ ЦВЕТ
ACCENT_COLOR = "#FFB300"    # Насыщенный янтарный
ACCENT_HOVER = "#E69900"    # Чуть темнее при наведении
ACCENT_PRESSED = "#CC8400"  # Глубокий оранжевый при нажатии
ACCENT_LIGHT = "#FFE082"    # Мягкий светлый янтарный для выделения в таблице

class App(QMainWindow):
    """Основное окно приложения с боковым меню."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление")
        self.setGeometry(100, 100, 1000, 700) 

        self.db = DBConnector()
        self.db.connect()

        self.model = model.Model()
        self.model.load_from_xml()

        self.load_stylesheet() # Применяем стили

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) 

        self.menu_widget = QWidget()
        self.menu_widget.setObjectName("MenuWidget") 
        self.menu_widget.setFixedWidth(180)
        
        self.menu_layout = QVBoxLayout(self.menu_widget)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(0) 

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("ContentWidget") 
        
        self.pages = [
            ("Главная", MainWidget(self.model)),
            ("Расходы", ExpensesWidget(self.model)),
            ("Склад", StorageWidget(self.model)),
            ("Товары", ProductsWidget(self.model)),
        ]
        
        self.menu_buttons = []

        for index, (name, widget) in enumerate(self.pages):
            self.stacked_widget.addWidget(widget)
            
            button = QPushButton(name)
            button.setObjectName(f"menuButton_{index}")
            button.clicked.connect(lambda checked, idx=index: self.stacked_widget.setCurrentIndex(idx))
            button.clicked.connect(lambda checked, btn=button: self.update_menu_style(btn))
            
            self.menu_layout.addWidget(button)
            self.menu_buttons.append(button)

        self.menu_layout.addStretch(1)

        main_layout.addWidget(self.menu_widget)
        main_layout.addWidget(self.stacked_widget)
        
        self.menu_buttons[0].setProperty("current", "true")
        self.menu_buttons[0].style().unpolish(self.menu_buttons[0])
        self.menu_buttons[0].style().polish(self.menu_buttons[0])

    def update_menu_style(self, active_button):
        """Обновляет стиль кнопок при переключении, чтобы выделить активную."""
        for button in self.menu_buttons:
            button.setProperty("current", "false")
            button.style().unpolish(button)
            button.style().polish(button)
        
        active_button.setProperty("current", "true")
        active_button.style().unpolish(active_button)
        active_button.style().polish(active_button)

    def closeEvent(self, event):
        """Обработка закрытия приложения для отключения от БД."""
        self.model.save_to_xml()    
        super().closeEvent(event)

    def load_stylesheet(self):
        """Загружает и применяет QSS для светлого стиля с глубоким янтарным акцентом."""
        style_sheet = f"""
        /* ОСНОВНОЙ СТИЛЬ */
        QWidget {{
            background-color: #F8F8F8; 
            color: #333333; 
            font-size: 10pt;
            selection-background-color: {ACCENT_COLOR}; /* Акцентный цвет при выделении */
            selection-color: #333333; 
        }}

        /* ------------------------------------------- */
        /* СТИЛЬ БОКОВОГО МЕНЮ */
        /* ------------------------------------------- */

        #MenuWidget {{ 
            background-color: #EFEFEF; 
            border-right: 1px solid #CCCCCC; 
        }}

        QPushButton {{ /* Стандартные кнопки (на страницах, включая "Добавить") */
            background-color: {ACCENT_COLOR}; /* ГЛУБОКИЙ ЯНТАРНЫЙ ФОН */
            color: #333333; /* ТЕМНЫЙ ТЕКСТ для лучшей читаемости */
            border: none;
            padding: 7px 12px;
            border-radius: 4px; 
            font-weight: bold; 
        }}

        QPushButton:hover {{
            background-color: {ACCENT_HOVER}; 
        }}
        
        QPushButton:pressed {{
            background-color: {ACCENT_PRESSED}; 
        }}
        
        /* (Стили кнопок меню) */
        QPushButton[objectName^="menuButton"] {{ 
            background-color: transparent; 
            color: #333333;
            border: none;
            text-align: left; 
            padding: 10px 15px; 
            font-weight: normal;
            border-left: 5px solid transparent; 
            border-radius: 0px; 
        }}
        
        QPushButton[objectName^="menuButton"]:hover {{
            background-color: #E0E0E0; 
        }}
        
        QPushButton[objectName^="menuButton"][current="true"] {{ 
            background-color: #FFFFFF; 
            border-left: 5px solid {ACCENT_COLOR}; /* ГЛУБОКИЙ ЯНТАРНЫЙ АКЦЕНТ! */
            font-weight: bold;
            color: #000000;
        }}

        /* ------------------------------------------- */
        /* СТИЛЬ КОНТЕНТА И ТАБЛИЦ */
        /* ------------------------------------------- */
        
        #ContentWidget {{ 
             background-color: #FFFFFF; 
             padding: 10px;
        }}
        
        QTableWidget::item:selected {{
            background-color: {ACCENT_LIGHT}; /* Мягкий светлый янтарный акцент для выделенной строки */
            color: #333333;
        }}
        
        /* (Остальные стили оставлены без изменений) */
        QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
            background-color: #FFFFFF; 
            color: #333333;
            border: 1px solid #CCCCCC; 
            padding: 3px;
            border-radius: 2px;
        }}
        
        QHeaderView::section {{
            background-color: #E0E0E0; 
            color: #333333;
            padding: 4px;
            border: 1px solid #CCCCCC;
        }}

        """
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style_sheet)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())