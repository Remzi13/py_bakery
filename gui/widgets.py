from PyQt6.QtWidgets import (
    QWidget, QTableWidget,  QHeaderView, QGroupBox, QVBoxLayout
)

class TableWidget(QWidget):

    def __init__(self, name, labels):
        super().__init__()
        self._name = name
        group = QGroupBox(self._name)
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(len(labels))
        self.table.setHorizontalHeaderLabels(labels)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)        
        group.setLayout(layout)

        layout = QVBoxLayout()
        layout.addWidget(group)
        self.setLayout(layout)

    def insertRow(self, pos):
        self.table.insertRow(pos)

    def setItem(self, row, column, item):
        self.table.setItem(row, column, item)

    def item(self, row, column):
        return self.table.item(row, column)
    
    def rowCount(self):
        return self.table.rowCount()
    
    def clear(self, rows):
        self.table.clearContents()
        self.table.setRowCount(rows)

    def selectedRows(self):
        return self.table.selectionModel().selectedRows()
    
    def itemSelection(self, fnc):
        self.table.itemSelectionChanged.connect(fnc)