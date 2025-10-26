import sys
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QTabWidget )

from db_connector import DBConnector

from gui.products import ProductsWidget
from gui.storage import StorageWidget
from gui.main_tab import MainWidget

from model import model

class App(QMainWindow):
    """Основное окно приложения."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление")
        self.setGeometry(100, 100, 800, 600)

        self.db = DBConnector()
        self.db.connect()

        self.model = model.Model()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        self.tab_widget.addTab(MainWidget(self.model), "Главная")
        self.tab_widget.addTab(StorageWidget(self.model), "Склад")
        self.tab_widget.addTab(ProductsWidget(self.model), "Товары")

    def closeEvent(self, event):
        """Обработка закрытия приложения для отключения от БД."""
        self.model.save_to_xml()
        self.db.disconnect()
        super().closeEvent(event)

if __name__ == '__main__':    
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())