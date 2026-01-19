import pytest
from contextlib import contextmanager

# Импортируем наш основной класс модели и вспомогательные функции
from sql_model.model import SQLiteModel
from sql_model.database import create_connection, initialize_db, get_unit_by_name

# Имя временной БД для тестов
TEST_DB = ':memory:'

# --- Фикстуры (Setup/Teardown) ---

@contextmanager
def setup_test_db():
    """
    Контекстный менеджер для создания временной базы данных в памяти
    и ее автоматического закрытия.
    """
    conn = create_connection(TEST_DB)
    try:
        initialize_db(conn)
        yield conn
    finally:
        conn.close()

@pytest.fixture
def clean_model():
    """
    Фикстура, которая создает чистый экземпляр SQLiteModel с БД в памяти 
    для каждого теста.
    """
    # SQLiteModel при инициализации вызывает create_connection и initialize_db
    model = SQLiteModel(db_file=TEST_DB)
    # Используем clean-up
    yield model
    model.close()


@pytest.fixture
def populated_model(clean_model: SQLiteModel):
    """
    Фикстура, которая создает модель с некоторыми заполненными данными.
    """
    model = clean_model
    
    # Вспомогательная функция для получения ID
    with setup_test_db() as conn:
        kg_id = get_unit_by_name(conn, 'kg')
        pc_id = get_unit_by_name(conn, 'pc')

    # 1. Добавляем ингредиенты (автоматически создаются StockItem и ExpenseType)
    model.stock().add('Мука', "Materials", 10, 'kg')
    model.stock().add('Яйцо', "Materials", 50, 'pc')
    
    # 3. Добавляем продукт (1 Хлеб = 1 kg Муки + 2 Яйца)
    recipe = [
        {'name': 'Мука', 'quantity': 1.0}, # 1 kg
        {'name': 'Яйцо', 'quantity': 2.0}  # 2 pcи
    ]
    model.products().add(name='Хлеб', price=200, materials=recipe)

    # 4. Добавляем другой продукт без ингредиентов (для проверки удаления)
    model.products().add(name='Вода', price=50, materials=[])

    # 5. Добавляем расход
    # В новой системе расход создается через документ
    # Для этого нам нужен ID поставщика и Unit
    model.suppliers().add(name="Supplier 1")
    supplier_id = model.suppliers().by_name("Supplier 1").id
    
    with setup_test_db() as conn: # Or reuse conn if possible, but safe here
         pass # No wait, we need units from DB
    
    cursor = model._conn.cursor()
    cursor.execute("SELECT id FROM units WHERE name='kg'")
    kg_id = cursor.fetchone()[0]

    et = model.expense_types().get("Мука") # created automatically by stock().add()
    
    items = [{
        'expense_type_id': et.id,
        'quantity': 5.0,
        'price': 50.0,
        'unit_id': kg_id 
    }]
    
    model.expense_documents().add(
        date="2025-01-01 10:00",
        supplier_id=supplier_id,
        total_amount=250.0, # 5 * 50
        comment="Test",
        items=items
    )
    
    return model


# --- Тесты ---

# 1. Тесты на CRUD материалов и связей (Stock, ExpenseTypes)
def test_material_add_and_relations(clean_model: SQLiteModel):
    """Тестирование добавления материала и его автоматических связей."""
    model = clean_model
    model.stock().add('Сахар', "Materials", 0, 'kg')

    # Проверка, что материал добавлен
    assert model.stock().get('Сахар') is not None
    # Проверка, что создан связанный StockItem
    assert model.stock().get('Сахар') is not None
    assert model.stock().get('Сахар').quantity == 0.0 # Изначально 0
    
    # Проверка, что создан связанный ExpenseType
    assert model.expense_types().get('Сахар') is not None
    
def test_material_delete(populated_model: SQLiteModel):
    """Тестирование удаления материала и проверки can_delete."""
    model = populated_model
    
    # Проверка: 'Мука' используется в 'Хлеб', удаление должно быть запрещено
    assert not model.stock().can_delete('Мука')
    with pytest.raises(ValueError):
        model.stock().delete('Мука')
        
    # Проверка: 'Вода' - это ингредиент, но не используется в продуктах (он был добавлен 
    # в 'populated_model' как продукт, но не как ингредиент). Добавим его как ингредиент 
    # для чистоты теста.
    model.stock().add('Соль', "Materials", 0, 'kg')
    assert model.stock().can_delete('Соль')

    # Удаление 'Соль'
    model.stock().delete('Соль')
    assert model.stock().len() == 2 # Мука и Яйцо остались
    assert model.stock().get('Соль') is None # Проверка, что запас удален
    assert model.expense_types().get('Соль') is None # Проверка, что тип расхода удален


# 2. Тесты на CRUD продуктов и рецептов
def test_product_add_and_update(populated_model: SQLiteModel):
    """Тестирование добавления и обновления продукта с рецептом."""
    model = populated_model
    
    # Проверка добавления
    assert model.products().by_name('Хлеб') is not None
    recipe = model.products().get_materials_for_product(model.products().by_name('Хлеб').id)
    assert len(recipe) == 2
    assert recipe[0]['name'] == 'Мука'
    assert recipe[0]['quantity'] == 1.0

    # Обновление продукта (изменяем цену и рецепт)
    new_recipe = [{'name': 'Мука', 'quantity': 0.5}]
    model.products().add(name='Хлеб', price=250, materials=new_recipe)
    
    updated_product = model.products().by_name('Хлеб')
    assert updated_product.price == 250
    
    # Проверка обновления рецепта
    updated_recipe = model.products().get_materials_for_product(updated_product.id)
    assert len(updated_recipe) == 1
    assert updated_recipe[0]['quantity'] == 0.5

def test_product_delete(populated_model: SQLiteModel):
    """Тестирование удаления продукта."""
    model = populated_model
    
    # Удаляем неиспользуемый продукт
    model.products().delete('Вода')
    assert model.products().has('Вода') is False

    # Добавляем продажу Хлеба, чтобы проверить запрет удаления
    model.sales().add(name='Хлеб', price=200, quantity=1.0, discount=0)
    with pytest.raises(ValueError):
        model.products().delete('Хлеб')
        

# 3. Тесты на бизнес-логику (Stock и Sales)
def test_stock_update_negative(populated_model: SQLiteModel):
    """Тестирование запрета отрицательного остатка на складе."""
    model = populated_model
    
    # Попытка списать больше, чем есть (Мука: 10 kg)
    # NOTE: В populated_model уже есть приход 5 кг муки из expense_documents (см. фикстуру)
    # И 10 кг начального остатка. Итого 15?
    # А, в фикстуре add('Мука', ..., 10, 'kg') устанавливает начальное значение.
    # Расход, если он помечен stock=True, увеличит остаток.
    # 'Мука' (ExpenseType) создается автоматически при add stock.
    # Проверим, какой stock у типа расхода 'Мука'.
    
    # При создании через stock().add() тип расхода по умолчанию stock=True? 
    # В StockRepository.add:
    # self._model.expense_types().add(name, 0, category_name, stock=True)
    # Да, stock=True.
    
    # Значит, добавление expense document (5 кг) увеличило запас.
    # Начально 10 + 5 = 15 кг.
    
    with pytest.raises(ValueError, match="Недостаточно запаса"):
        model.stock().update('Мука', -100.0)

def test_sales_and_stock_logic(populated_model: SQLiteModel):
    """Тестирование списания ингредиентов при продаже."""
    model = populated_model
    
    # Начальный запас
    initial_flour = model.stock().get('Мука').quantity 
    initial_egg = model.stock().get('Яйцо').quantity   
    
    # Продажа 2-х единиц "Хлеб" (1 Хлеб = 1 kg Муки + 2 Яйца)
    # Списание: Мука: 1*2=2 kg, Яйца: 2*2=4 шт.
    model.sales().add(name='Хлеб', price=200, quantity=2.0, discount=0)
    
    # Проверка списания
    final_flour = model.stock().get('Мука').quantity
    final_egg = model.stock().get('Яйцо').quantity
    
    assert model.sales().len() == 1
    assert final_flour == initial_flour - 2.0  
    assert final_egg == initial_egg - 4.0      
    
    # Проверка ошибки при недостатке запаса
    # Попытка продать 30 шт. "Хлеб" (нужно 30*1=30 kg Муки, есть ~13)
    with pytest.raises(ValueError, match="Недостаточно запаса"):
        model.sales().add(name='Хлеб', price=200, quantity=100.0, discount=0)


# 4. Тесты на финансовые расчеты
def test_finance_calculations(populated_model: SQLiteModel):
    """Тестирование расчетов дохода, расхода и прибыли."""
    model = populated_model
    
    # Продажи:
    # 1. Продажа Хлеба (цена 200, кол-во 1, скидка 0) -> Доход: 200 * 1 = 200
    model.sales().add(name='Хлеб', price=200, quantity=1.0, discount=0) 
    
    # 2. Продажа Хлеба (цена 200, кол-во 2, скидка 10%) -> Доход: 200 * 2 * (1 - 0.1) = 360
    model.sales().add(name='Хлеб', price=200, quantity=2.0, discount=10) 
    
    # Общий Доход = 200 + 360 = 560
    assert model.calculate_income() == 560.0
    
    # Расходы (уже добавлен в populated_model):
    # Мука: цена 50, кол-во 5.0 -> Расход: 5 * 50 = 250
    # Изначально 'populated_model' создал документ на 250.
    assert model.calculate_expenses() == 250.0
    
    # Прибыль = Доход - Расход = 560 - 250 = 310
    assert model.calculate_profit() == 310.0
    
    # Добавляем еще один расход (другой тип)
    model.expense_types().add(name='Аренда', default_price=1000, category_name='Utilities')
    et_rent = model.expense_types().get('Аренда')
    
    # We need to add document for this
    supplier_id = model.suppliers().by_name("Supplier 1").id
    # No items needed for just expense value? Using Items logic
    # But wait, do we support expenses without items? 
    # model.expense_documents().add(..., items=[]) -> total_amount is explicit arg
    
    cursor = model._conn.cursor()
    cursor.execute("SELECT id FROM units WHERE name='pc'") 
    pc_id = cursor.fetchone()[0]

    model.expense_documents().add(
         date="2025-01-02",
         supplier_id=supplier_id,
         total_amount=1000.0, # Explicit total
         comment="Rent",
         items=[{
             'expense_type_id': et_rent.id,
             'quantity': 1.0,
             'price': 1000.0,
             'unit_id': pc_id
         }]
    )
    
    # Общий Расход = 250 + 1000 = 1250
    assert model.calculate_expenses() == 1250.0
    
    # Новая Прибыль = 560 - 1250 = -690
    assert model.calculate_profit() == -690.0