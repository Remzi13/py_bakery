from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QTableWidget, QMessageBox, QTableWidgetItem
)

class SQLRequestWidget(QWidget):
    
    def __init__(self, model):
        super().__init__() 
        self._model = model

        layout = QVBoxLayout(self)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Введите SQL-запрос, например: SELECT * FROM users;")

        self.run_button = QPushButton("Выполнить")
        self.run_button.clicked.connect(self.execute_query)

        self.table = QTableWidget()

        layout.addWidget(self.query_input)
        layout.addWidget(self.run_button)
        layout.addWidget(self.table)

    def execute_query(self):
        query = self.query_input.text().strip()
        if not query:
            return

        try:
            rows, headers = self._model.request(query)
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))