# main_app.py
import sys
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QTabWidget )

from db_connector import DBConnector # Импортируем наш класс для работы с БД

from gui.products import ProductsWidget

from model import model

class BakeryApp(QMainWindow):
    """Основное окно приложения."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление")
        self.setGeometry(100, 100, 800, 600)

        # 1. Подключение к базе данных
        self.db = DBConnector()
        self.db.connect()

        self.model = model.Model()  # Инициализация модели данных   

        # 2. Создание главного виджета с вкладками
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 3. Добавление вкладок        
        self.tab_widget.addTab(ProductsWidget(self.model), "2. Продукция ")

    def closeEvent(self, event):
        """Обработка закрытия приложения для отключения от БД."""
        self.model.save_to_xml()
        self.db.disconnect()
        super().closeEvent(event)


if __name__ == '__main__':    
    app = QApplication(sys.argv)
    window = BakeryApp()
    window.show()
    sys.exit(app.exec())