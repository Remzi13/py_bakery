from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QTableWidget, QMessageBox, QTableWidgetItem
)

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout

class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []

        # --- Форматы ---
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0077cc"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#009933"))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#cc5500"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#999999"))
        comment_format.setFontItalic(True)

        # --- SQL ключевые слова ---
        keywords = [
            "SELECT", "FROM", "WHERE", "AND", "OR", "INSERT", "INTO", "VALUES",
            "UPDATE", "SET", "DELETE", "CREATE", "TABLE", "DROP", "ALTER",
            "PRIMARY", "KEY", "FOREIGN", "NOT", "NULL", "JOIN", "LEFT", "RIGHT",
            "INNER", "OUTER", "GROUP", "BY", "ORDER", "LIMIT", "DISTINCT",
            "AS", "ON", "IN", "IS", "LIKE"
        ]

        for word in keywords:
            pattern = QRegularExpression(rf"\b{word}\b", QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, keyword_format))

        # --- SQL функции ---
        functions = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
        for func in functions:
            pattern = QRegularExpression(rf"\b{func}\b", QRegularExpression.PatternOption.CaseInsensitiveOption)
            self.highlighting_rules.append((pattern, function_format))

        # --- Строки ---
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), string_format))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # --- Комментарии ---
        self.highlighting_rules.append((QRegularExpression(r"--[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class SQLRequestWidget(QWidget):
    
    def __init__(self, model):
        super().__init__() 
        self._model = model

        layout = QVBoxLayout(self)

        self.query_input = QTextEdit()
        self.highlighter = SqlHighlighter(self.query_input.document())
        self.query_input.setPlaceholderText("Введите SQL-запрос, например: SELECT * FROM users;")

        self.run_button = QPushButton("Выполнить")
        self.run_button.clicked.connect(self.execute_query)

        self.table = QTableWidget()

        layout.addWidget(self.query_input)
        layout.addWidget(self.run_button)
        layout.addWidget(self.table)

    def execute_query(self):
        query = self.query_input.toPlainText().strip()
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