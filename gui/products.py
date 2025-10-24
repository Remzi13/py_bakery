from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTabWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHeaderView
)

import model.model as model

class IngredientsTab(QWidget):
    def __init__(self, model):
        super().__init__()
        
        self.model = model
        add_layout = QGridLayout()

        self.name_input = QLineEdit()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(model.get_units())
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_ingredient)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Название", "Ед. изм."])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        add_layout.addWidget(QLabel("Название:"), 0, 0)
        add_layout.addWidget(self.name_input, 0, 1)
        add_layout.addWidget(QLabel("Ед. измерения:"), 1, 0)
        add_layout.addWidget(self.unit_combo, 1, 1)
        add_layout.addWidget(self.add_button, 2, 0, 1, 2)
        add_layout.addWidget(QLabel("Склад:"), 3, 0, 1, 2)
        add_layout.addWidget(self.table, 4, 0, 1, 2) 

        self.setLayout(add_layout)

    def add_ingredient(self):        

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название ингредиента.")
            return
        
        self.model.add_ingredient(self.name_input.text().strip(), self.unit_combo.currentIndex())
        data = self.model.get_ingredients()
        self.table.clearContents()
        self.table.setRowCount(len(data))
        i = 0
        for row in data:            
            self.table.setItem(i, 0, QTableWidgetItem(row['name']))
            self.table.setItem(i, 1, QTableWidgetItem(self.model.get_units()[row['unit']]))
            i = i + 1
        

        

        # Очистить поля ввода
        self.name_input.clear()
        self.unit_combo.setCurrentIndex(0)

class ProductsTab(QWidget):
    
    def __init__(self, model):
        super().__init__()        
        
        main_layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)        

        # 1. Форма для добавления нового ингредиента
       
        self.tab_widget.addTab(IngredientsTab(model), "Ингредиенты")
        
        ## 2. Форма для добавления новой продукции
        #add_product_group = QGroupBox("2. Добавить новую продукцию")
        #add_layout = QGridLayout()
#
        #self.prod_name_input = QLineEdit()
        #self.prod_price_input = QLineEdit()
        #self.add_prod_button = QPushButton("Добавить Продукт")
        #self.add_prod_button.clicked.connect(self.add_new_product)
#
        #add_layout.addWidget(QLabel("Название:"), 0, 0)
        #add_layout.addWidget(self.prod_name_input, 0, 1)
        #add_layout.addWidget(QLabel("Цена (за шт.):"), 1, 0)
        #add_layout.addWidget(self.prod_price_input, 1, 1)
        #add_layout.addWidget(self.add_prod_button, 2, 0, 1, 2)
        #
        #add_product_group.setLayout(add_layout)
        #main_layout.addWidget(add_product_group)
        #
        ## 2. Форма для создания/редактирования рецепта
        #recipe_group = QGroupBox("2. Создать/Редактировать Рецепт")
        #recipe_layout = QGridLayout()
        #
        #self.product_select_combo = QComboBox() # Выбор продукта для рецепта
        #self.ingredient_for_recipe_combo = QComboBox() # Выбор ингредиента
        #self.quantity_needed_input = QLineEdit() # Количество ингредиента
        #self.add_recipe_button = QPushButton("Добавить Ингредиент в Рецепт")
        #self.add_recipe_button.clicked.connect(self.add_ingredient_to_recipe)
        #
        #self.recipe_table = QTableWidget()
        #self.recipe_table.setColumnCount(3)
        #self.recipe_table.setHorizontalHeaderLabels(["Ингредиент", "Количество", "Ед. изм."])
        #self.recipe_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
#
        #recipe_layout.addWidget(QLabel("Продукт:"), 0, 0)
        #recipe_layout.addWidget(self.product_select_combo, 0, 1)
        #recipe_layout.addWidget(QLabel("Ингредиент:"), 1, 0)
        #recipe_layout.addWidget(self.ingredient_for_recipe_combo, 1, 1)
        #recipe_layout.addWidget(QLabel("Нужно (доли):"), 2, 0)
        #recipe_layout.addWidget(self.quantity_needed_input, 2, 1)
        #recipe_layout.addWidget(self.add_recipe_button, 3, 0, 1, 2)
        #
        #recipe_layout.addWidget(QLabel("Состав Рецепта:"), 4, 0, 1, 2)
        #recipe_layout.addWidget(self.recipe_table, 5, 0, 1, 2)
        #
        #recipe_group.setLayout(recipe_layout)
        #main_layout.addWidget(recipe_group)
#
        self.setLayout(main_layout)        
    


    def add_new_product(self):
        pass  # Логика добавления нового продукта в БД

    def add_ingredient_to_recipe(self):
        pass  # Логика добавления ингредиента в рецепт продукта