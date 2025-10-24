# main_app.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, 
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, 
    QTableWidgetItem, QMessageBox, QGroupBox, QHBoxLayout,
    QHeaderView
)
from PyQt6.QtCore import Qt
from db_connector import DBConnector # Импортируем наш класс для работы с БД
from datetime import datetime

from gui.products import ProductsTab

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
        self.tab_widget.addTab(ProductsTab(self.model), "2. Продукция (Рецепты)")

    def closeEvent(self, event):
        """Обработка закрытия приложения для отключения от БД."""
        self.db.disconnect()
        super().closeEvent(event)


if __name__ == '__main__':    
    app = QApplication(sys.argv)
    window = BakeryApp()
    window.show()
    sys.exit(app.exec())