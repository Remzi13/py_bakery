import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QPushButton, 
    QMessageBox, QLineEdit, QFormLayout, QLabel,
    QDialog, QDialogButtonBox, QAbstractItemView # <-- ИМПОРТИРУЕМ QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from typing import Optional, List, Tuple

# Предполагаем, что ваша модель находится в корневом каталоге
from sql_model.model import SQLiteModel
from sql_model.entities import Supplier

# --- Дополнительный Диалог для Редактирования (Полный набор полей) ---

class SupplierEditDialog(QDialog):
    """Диалог для ввода или редактирования всех полей поставщика."""
    
    def __init__(self, edit, current_supplier: Optional[Supplier] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Редактировать поставщика" if current_supplier else "Добавить поставщика")
        self.current_supplier = current_supplier
        
        # Поля ввода
        if edit:
            self.name_input = QLineEdit()
        else:
            self.name_input = QLabel()
            
        self.contact_person_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        # Если мы редактируем, заполняем поля текущими значениями
        if current_supplier:
            self.name_input.setText(current_supplier.name)
            self.contact_person_input.setText(current_supplier.contact_person or '')
            self.phone_input.setText(current_supplier.phone or '')
            self.email_input.setText(current_supplier.email or '')
            self.address_input.setText(current_supplier.address or '')
            
        # Макет
        layout = QFormLayout(self)
        layout.addRow("Имя поставщика (*):", self.name_input)
        layout.addRow("Контактное лицо:", self.contact_person_input)
        layout.addRow("Телефон:", self.phone_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Адрес:", self.address_input)
        
        # Кнопки OK/Cancel
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self) -> Tuple[str, str, str, str, str]:
        """Возвращает данные из полей ввода."""
        return (
            self.name_input.text().strip(),
            self.contact_person_input.text().strip() or None,
            self.phone_input.text().strip() or None,
            self.email_input.text().strip() or None,
            self.address_input.text().strip() or None,
        )


class SuppliersWidget(QWidget):
    """
    Виджет для управления поставщиками (CRUD) с использованием QTableWidget и QDialog.
    """
    
    HEADERS = ["ID", "Имя", "Контактное лицо", "Телефон", "Email", "Адрес"]
    
    def __init__(self, model: SQLiteModel):
        super().__init__()
        self.model = model
        self.suppliers_repo = self.model.suppliers()
        self.setWindowTitle("Управление поставщиками")
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Настройка элементов интерфейса (таблица и кнопки)."""
        main_layout = QVBoxLayout(self)
        
        # 1. Таблица для отображения поставщиков
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        
        # Скрываем столбец ID
        self.table.setColumnHidden(0, True) 
                
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Связываем двойной клик с функцией редактирования
        self.table.doubleClicked.connect(self.edit_supplier_dialog)
        
        buttons_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_supplier_dialog)
        buttons_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_supplier_dialog)
        buttons_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_supplier)
        buttons_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.table)
        
        # Добавляем подгонку ширины
        self.table.horizontalHeader().setStretchLastSection(True)


    def load_data(self):
        """Загружает все данные о поставщиках из БД и заполняет таблицу."""
        data: List[Supplier] = self.suppliers_repo.data()
        self.table.setRowCount(len(data))
        
        for row_index, supplier in enumerate(data):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(supplier.id)))
            self.table.setItem(row_index, 1, QTableWidgetItem(supplier.name))
            self.table.setItem(row_index, 2, QTableWidgetItem(supplier.contact_person or ''))
            self.table.setItem(row_index, 3, QTableWidgetItem(supplier.phone or ''))
            self.table.setItem(row_index, 4, QTableWidgetItem(supplier.email or ''))
            self.table.setItem(row_index, 5, QTableWidgetItem(supplier.address or ''))

        self.table.resizeColumnsToContents()

    # --- Диалоги и операции ---

    def add_supplier_dialog(self):
        """Открывает диалог для добавления нового поставщика."""
        dialog = SupplierEditDialog(True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, contact, phone, email, address = dialog.get_data()
            
            if not name:
                QMessageBox.warning(self, "Ошибка ввода", "Имя поставщика обязательно.")
                return

            try:
                self.suppliers_repo.add(
                    name=name, 
                    contact_person=contact, 
                    phone=phone, 
                    email=email, 
                    address=address
                )
                QMessageBox.information(self, "Успех", f"Поставщик '{name}' добавлен.")
                self.load_data()
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка добавления", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Критическая ошибка", f"Не удалось добавить поставщика: {e}")


    def edit_supplier_dialog(self):
        """Открывает диалог для редактирования выбранного поставщика."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:            
            return

        row = selected_rows[0].row()
        supplier_id_str = self.table.item(row, 0).text()
        supplier_id = int(supplier_id_str)
        
        current_supplier = self.suppliers_repo.get(supplier_id)
        if not current_supplier:
            QMessageBox.warning(self, "Ошибка", "Поставщик не найден в базе данных.")
            self.load_data()
            return
            
        dialog = SupplierEditDialog(False, current_supplier)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, contact, phone, email, address = dialog.get_data()
            
            if not name:
                QMessageBox.warning(self, "Ошибка ввода", "Имя поставщика обязательно.")
                return

            try:
                self.suppliers_repo.update(
                    supplier_id=supplier_id,
                    name=name,
                    contact_person=contact,
                    phone=phone,
                    email=email,
                    address=address
                )
                QMessageBox.information(self, "Успех", f"Поставщик '{name}' обновлен.")
                self.load_data()
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка редактирования", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Критическая ошибка", f"Не удалось обновить поставщика: {e}")


    def delete_supplier(self):
        """Удаляет выбранного поставщика после подтверждения."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите поставщика для удаления.")
            return
            
        row = selected_rows[0].row()
        name_to_delete = self.table.item(row, 1).text()

        # Запрос подтверждения
        reply = QMessageBox.question(self, 'Подтверждение удаления', 
                                     f"Вы действительно хотите удалить поставщика '{name_to_delete}'? ", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.suppliers_repo.delete(name_to_delete)
                QMessageBox.information(self, "Успех", f"Поставщик '{name_to_delete}' удален.")
                self.load_data()
            except Exception as e:
                # Если поставщик связан с расходами, SQLite выдаст ошибку
                QMessageBox.critical(self, "Ошибка удаления", 
                                     f"Не удалось удалить '{name_to_delete}'. Проверьте, нет ли связанных расходов. Ошибка: {e}")

