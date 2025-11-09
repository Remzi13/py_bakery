import os
import logging
import sys
import traceback

from PyQt6.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QPushButton, QStackedWidget, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

# Импортируем классы вкладок
from gui.products_tab import ProductsWidget
from gui.stock_tab import StorageWidget
from gui.expenses_tab import ExpensesWidget
from gui.main_tab import MainWidget
from gui.sqlrequest_tab import SQLRequestWidget
from gui.suppliers_tab import SuppliersWidget

from sql_model.model import SQLiteModel


# ГЛОБАЛЬНЫЕ ЦВЕТА (СДЕРЖАННАЯ НЕЙТРАЛЬНАЯ ПАЛИТРА)
ACCENT_COLOR = "#333333"    # Темно-Серый (почти Черный, для основных акцентов)
ACCENT_HOVER = "#555555"    # Чуть светлее Темно-Серого (при наведении)
ACCENT_PRESSED = "#111111"  # Самый темный цвет (при нажатии)
ACCENT_LIGHT = "#EEEEEE"    # Очень Светло-Серый (для фона при наведении/выделении)
DARK_TEXT = "#333333"       # Основной темный текст
LIGHT_BG = "#F5F5F5"        # Очень Светлый Фон (боковое меню)
WINDOW_BG = "#FFFFFF"       # Белый Фон (основное окно и контент)


# 1. Настройка логирования (без изменений)
LOG_FILE = 'app_errors.log'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s | %(levelname)s | %(threadName)s | %(name)s | %(message)s'
)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик исключений для PyQt6."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Необработанное исключение:", exc_info=(exc_type, exc_value, exc_traceback))
    
    error_message = f"Произошла критическая ошибка: {exc_value}\n\nПодробности записаны в {LOG_FILE}"
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Критическая ошибка приложения")
    msg.setText(error_message)
    msg.exec()


class App(QMainWindow):

    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Менеджер Пекарни")
        self.setGeometry(100, 100, 1000, 700) 

        self.model = model
        self.current_button = None

        self._create_widgets()
        self._create_layout()
        self._connect_signals()
        
        self.load_stylesheet() 
        
        self.setup_icon()

        self.switch_tab(0)

    def setup_icon(self):
        """Устанавливает иконку для окна приложения."""
        ICON_FILE = "bakery_manager.ico"
        if os.path.exists(ICON_FILE):
            app_icon = QIcon(ICON_FILE)
            self.setWindowIcon(app_icon)
        else:
            logging.warning(f"Файл иконки '{ICON_FILE}' не найден. Используется иконка по умолчанию.")

    def _create_widgets(self):
        """Создает виджеты главного окна."""
        
        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentWidget")
        
        # Создание экземпляров вкладок
        self.main_tab = MainWidget(self.model)
        self.products_tab = ProductsWidget(self.model)
        self.stock_tab = StorageWidget(self.model)
        self.expenses_tab = ExpensesWidget(self.model)
        self.sql_tab = SQLRequestWidget(self.model)
        self.suppliers_tab = SuppliersWidget(self.model)
        
        # Добавление в стек
        self.stack.addWidget(self.main_tab)
        self.stack.addWidget(self.products_tab)
        self.stack.addWidget(self.stock_tab)
        self.stack.addWidget(self.expenses_tab)
        self.stack.addWidget(self.suppliers_tab)
        self.stack.addWidget(self.sql_tab)
        
        
        # Кнопки меню
        self.menu_buttons = []
        self.tabs_info = [
            ("Главная", 0),
            ("Продукция", 1),
            ("Склад", 2),
            ("Расходы", 3),
            ("Поставшики", 4),
            ("SQL-Запрос", 5)
        ]
        
        for name, index in self.tabs_info:
            btn = QPushButton(name)
            btn.setObjectName(f"menuButton_{index}")
            btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(35) 
            self.menu_buttons.append(btn)
            
    def _create_layout(self):
        """Организует расположение виджетов."""
        
        self.menu_widget = QWidget()
        self.menu_widget.setObjectName("MenuWidget")
        self.menu_layout = QVBoxLayout(self.menu_widget)
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        for btn in self.menu_buttons:
            self.menu_layout.addWidget(btn)
        
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.menu_widget.setFixedWidth(130) 
        main_layout.addWidget(self.menu_widget)
        main_layout.addWidget(self.stack, 1) 
        
        self.setCentralWidget(main_widget)

    def _connect_signals(self):
        """Соединяет сигналы кнопок с переключением вкладок."""
        for index, btn in enumerate(self.menu_buttons):
            btn.clicked.connect(lambda _, i=index: self.switch_tab(i))

    def switch_tab(self, index):
        """Переключает вкладки и обновляет стили кнопок меню."""
        
        if self.current_button is not None:
            self.current_button.setProperty("current", "false")
            self.current_button.style().polish(self.current_button)

        self.current_button = self.menu_buttons[index]
        self.current_button.setProperty("current", "true")
        self.current_button.style().polish(self.current_button)
        
        self.stack.setCurrentIndex(index)


    def load_stylesheet(self):
        """Загружает и применяет QSS для сдержанной нейтральной палитры (с исправленными слайдерами)."""
        
        style_sheet = f"""
        /* ОСНОВНОЙ СТИЛЬ */
        QWidget {{
            background-color: {LIGHT_BG}; 
            color: {DARK_TEXT}; 
            font-size: 9pt; 
            font-family: "Segoe UI", "Arial", sans-serif;
            selection-background-color: {ACCENT_LIGHT}; 
            selection-color: {DARK_TEXT}; 
        }}
        
        QMainWindow, QDialog {{
            background-color: {WINDOW_BG}; 
        }}
        
        /* ------------------------------------------- */
        /* СТИЛЬ БОКОВОГО МЕНЮ */
        /* ------------------------------------------- */

        #MenuWidget {{ 
            background-color: #EEEEEE; 
            border-right: 1px solid #CCCCCC; 
        }}
        
        QPushButton[objectName^="menuButton"] {{ 
            background-color: transparent; 
            color: {DARK_TEXT};
            border: none;
            text-align: left; 
            padding: 8px 10px; 
            font-weight: normal;
            border-left: 3px solid transparent; 
            border-radius: 0px; 
        }}
        
        QPushButton[objectName^="menuButton"]:hover {{
            background-color: #E0E0E0; 
        }}
        
        QPushButton[objectName^="menuButton"][current="true"] {{ 
            background-color: {WINDOW_BG}; 
            border-left: 3px solid {ACCENT_COLOR}; 
            font-weight: bold;
            color: {ACCENT_COLOR};
        }}
        
        /* ------------------------------------------- */
        /* СТИЛЬ КНОПОК ДЕЙСТВИЙ */
        /* ------------------------------------------- */
        
        QPushButton {{ 
            background-color: {WINDOW_BG}; 
            color: {ACCENT_HOVER}; 
            border: 1px solid #CCCCCC; 
            padding: 5px 10px; 
            border-radius: 4px; 
            font-weight: bold; 
        }}

        QPushButton:hover {{
            background-color: {ACCENT_LIGHT}; 
            border: 1px solid {ACCENT_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: {ACCENT_COLOR}; 
            color: {WINDOW_BG}; 
        }}
        
        QPushButton[class="SecondaryButton"] {{ 
            background-color: {WINDOW_BG}; 
            color: #AAAAAA; 
            border: 1px solid #E0E0E0; 
            font-weight: normal;
        }}
        
        QPushButton[class="SecondaryButton"]:hover {{
            background-color: {ACCENT_LIGHT}; 
        }}
        
        QPushButton[class="SecondaryButton"]:pressed {{
            background-color: #CCCCCC; 
            color: {DARK_TEXT};
        }}

        /* ------------------------------------------- */
        /* СТИЛЬ QMESSAGEBOX */
        /* ------------------------------------------- */
        
        QMessageBox {{
            background-color: {WINDOW_BG}; 
            color: {DARK_TEXT};
        }}
        
        QMessageBox QLabel {{
            color: {DARK_TEXT};
            padding: 5px;
        }}
        
        /* ------------------------------------------- */
        /* СТИЛЬ QSCROLLBAR (СЛАЙДЕРЫ) */
        /* ------------------------------------------- */
        
        /* Вертикальный скроллбар */
        QScrollBar:vertical {{
            border: none;
            background: #F0F0F0; /* Очень светлый трек скроллбара */
            width: 8px; 
            margin: 0px; 
        }}

        /* Ручка (сам слайдер) */
        QScrollBar::handle:vertical {{
            background: {ACCENT_LIGHT}; /* Очень светло-серый (статичный) */
            min-height: 20px;
            border-radius: 4px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: #CCCCCC; /* Чуть темнее при наведении */
        }}

        QScrollBar::handle:vertical:pressed {{
            background: {ACCENT_HOVER}; /* Темно-серый при нажатии */
        }}

        /* Удаление кнопок (стрелок) для современного вида */
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        /* Горизонтальный скроллбар (для полноты) */
        QScrollBar:horizontal {{
            border: none;
            background: #F0F0F0; 
            height: 8px;
            margin: 0px; 
        }}

        QScrollBar::handle:horizontal {{
            background: {ACCENT_LIGHT}; 
            min-width: 20px;
            border-radius: 4px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: #CCCCCC;
        }}

        QScrollBar::handle:horizontal:pressed {{
            background: {ACCENT_HOVER}; 
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
            width: 0px;
        }}
        
        /* ------------------------------------------- */
        /* СТИЛЬ QTabWidget */
        /* ------------------------------------------- */
        
        QTabWidget::pane {{ 
            border: 1px solid #CCCCCC;
            background-color: {WINDOW_BG};
        }}

        QTabBar::tab {{ 
            background-color: #F0F0F0;
            color: {DARK_TEXT};
            padding: 6px 12px; 
            border: 1px solid #CCCCCC;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 1px;
        }}

        QTabBar::tab:selected {{ 
            background-color: {WINDOW_BG}; 
            color: {ACCENT_COLOR}; 
            font-weight: bold;
            border-top: 2px solid {ACCENT_COLOR}; 
            border-left: 1px solid #CCCCCC; 
            border-right: 1px solid #CCCCCC; 
            border-bottom: none;
            padding-top: 5px; 
        }}

        QTabBar::tab:hover {{
            background-color: #E0E0E0;
        }}
        
        /* ------------------------------------------- */
        /* СТИЛЬ ПОЛЕЙ ВВОДА и QComboBox */
        /* ------------------------------------------- */
        
        QLineEdit, QDoubleSpinBox, QSpinBox, QTextEdit {{
            background-color: #FFFFFF; 
            border: 1px solid #CCCCCC; 
            padding: 4px; 
            border-radius: 4px;
        }}
        
        QComboBox {{
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            padding: 4px; 
            border-radius: 4px;
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: center right; 
            width: 18px; 
            border-left-width: 1px;
            border-left-color: #CCCCCC;
            border-left-style: solid; 
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }}
        
        QComboBox::down-arrow {{
            image: none; 
            border-style: solid;
            border-width: 0px;
            border-top-width: 5px; 
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top-color: {ACCENT_HOVER}; 
            width: 0px;
            height: 0px;
            padding-right: 3px;
        }}

        QComboBox:on {{ 
            border: 1px solid {ACCENT_HOVER};
        }}
        
        QComboBox QAbstractItemView {{ 
            border: 1px solid {ACCENT_HOVER};
            selection-background-color: {ACCENT_LIGHT}; 
            selection-color: {DARK_TEXT};
            background-color: {WINDOW_BG};
            min-height: 40px; 
            padding: 3px;
        }}
        
        /* ------------------------------------------- */
        /* СТИЛЬ ТАБЛИЦ И ГРУПП */
        /* ------------------------------------------- */
        
        #ContentWidget {{ 
             background-color: {WINDOW_BG}; 
             padding: 10px; 
        }}
        
        QGroupBox {{
            border: 1px solid #E0E0E0; 
            border-radius: 4px;
            margin-top: 10px; 
            padding-top: 8px;
            padding-left: 4px;
            padding-right: 4px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left; 
            padding: 0 5px;
            margin-left: 5px;
            color: {ACCENT_HOVER}; 
            font-weight: bold;
        }}

        QTableWidget::item:selected {{
            background-color: {ACCENT_LIGHT}; 
            color: {DARK_TEXT};
        }}
        
        QHeaderView::section {{
            background-color: #E0E0E0; 
            color: {DARK_TEXT};
            padding: 5px; 
            border: 1px solid #CCCCCC;
        }}
        
        QLabel {{
            padding: 1px;
        }}


        """
        app = QApplication.instance()
        if app:
            app.setStyleSheet(style_sheet)

    
# -----------------------------------------------------------
# ЗАПУСК ПРИЛОЖЕНИЯ
# -----------------------------------------------------------
def main():
    #sys.excepthook = handle_exception
    
    app = QApplication(sys.argv)
    
    font = QFont("Arial", 9) 
    app.setFont(font)

    try:
        model = SQLiteModel("bakery.db")        
    except Exception as e:
        logging.critical(f"Ошибка инициализации модели/базы данных: {e}", exc_info=True)
        QMessageBox.critical(None, "Ошибка базы данных", 
                             f"Не удалось инициализировать базу данных. Проверьте логи: {e}")
        return

    window = App(model)
    window.show()
    sys.exit(app.exec())
 

if __name__ == '__main__':
    main()