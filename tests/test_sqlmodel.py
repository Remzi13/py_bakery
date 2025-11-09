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
        kg_id = get_unit_by_name(conn, 'кг')
        штук_id = get_unit_by_name(conn, 'штук')

    # 1. Добавляем ингредиенты (автоматически создаются StockItem и ExpenseType)
    model.ingredients().add(name='Мука', unit_name='кг')
    model.ingredients().add(name='Яйцо', unit_name='штук')
    
    # 2. Оприходуем запас (Мука: 10 кг, Яйцо: 50 штук)
    model.stock().update('Мука', 10.0)
    model.stock().update('Яйцо', 50.0)
    
    # 3. Добавляем продукт (1 Хлеб = 1 кг Муки + 2 Яйца)
    recipe = [
        {'name': 'Мука', 'quantity': 1.0}, # 1 кг
        {'name': 'Яйцо', 'quantity': 2.0}  # 2 штуки
    ]
    model.products().add(name='Хлеб', price=200, ingredients=recipe)

    # 4. Добавляем другой продукт без ингредиентов (для проверки удаления)
    model.products().add(name='Вода', price=50, ingredients=[])

    # 5. Добавляем расход
    model.expenses().add(name='Мука', price=50, quantity=5.0, supplier_name=None) # Покупка 5 кг муки по 50
    
    return model


# --- Тесты ---

# 1. Тесты на CRUD ингредиентов и связей (Stock, ExpenseTypes)
def test_ingredient_add_and_relations(clean_model: SQLiteModel):
    """Тестирование добавления ингредиента и его автоматических связей."""
    model = clean_model
    model.ingredients().add(name='Сахар', unit_name='кг')

    # Проверка, что ингредиент добавлен
    assert model.ingredients().len() == 1
    assert model.ingredients().by_name('Сахар').name == 'Сахар'
    
    # Проверка, что создан связанный StockItem
    assert model.stock().get('Сахар') is not None
    assert model.stock().get('Сахар').quantity == 0.0 # Изначально 0
    
    # Проверка, что создан связанный ExpenseType
    assert model.expense_types().get('Сахар') is not None
    
def test_ingredient_delete(populated_model: SQLiteModel):
    """Тестирование удаления ингредиента и проверки can_delete."""
    model = populated_model
    
    # Проверка: 'Мука' используется в 'Хлеб', удаление должно быть запрещено
    assert not model.ingredients().can_delete('Мука')
    with pytest.raises(ValueError):
        model.ingredients().delete('Мука')
        
    # Проверка: 'Вода' - это ингредиент, но не используется в продуктах (он был добавлен 
    # в 'populated_model' как продукт, но не как ингредиент). Добавим его как ингредиент 
    # для чистоты теста.
    model.ingredients().add(name='Соль', unit_name='кг')
    assert model.ingredients().can_delete('Соль')

    # Удаление 'Соль'
    model.ingredients().delete('Соль')
    assert model.ingredients().len() == 2 # Мука и Яйцо остались
    assert model.stock().get('Соль') is None # Проверка, что запас удален
    assert model.expense_types().get('Соль') is None # Проверка, что тип расхода удален


# 2. Тесты на CRUD продуктов и рецептов
def test_product_add_and_update(populated_model: SQLiteModel):
    """Тестирование добавления и обновления продукта с рецептом."""
    model = populated_model
    
    # Проверка добавления
    assert model.products().by_name('Хлеб') is not None
    recipe = model.products().get_ingredients_for_product(model.products().by_name('Хлеб').id)
    assert len(recipe) == 2
    assert recipe[0]['name'] == 'Мука'
    assert recipe[0]['quantity'] == 1.0

    # Обновление продукта (изменяем цену и рецепт)
    new_recipe = [{'name': 'Мука', 'quantity': 0.5}]
    model.products().add(name='Хлеб', price=250, ingredients=new_recipe)
    
    updated_product = model.products().by_name('Хлеб')
    assert updated_product.price == 250
    
    # Проверка обновления рецепта
    updated_recipe = model.products().get_ingredients_for_product(updated_product.id)
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
    
    # Попытка списать больше, чем есть (Мука: 10 кг)
    with pytest.raises(ValueError, match="Недостаточно запаса"):
        model.stock().update('Мука', -100.0)

def test_sales_and_stock_logic(populated_model: SQLiteModel):
    """Тестирование списания ингредиентов при продаже."""
    model = populated_model
    
    # Начальный запас
    initial_flour = model.stock().get('Мука').quantity # 10.0 кг
    initial_egg = model.stock().get('Яйцо').quantity   # 50.0 штук
    
    # Продажа 2-х единиц "Хлеб" (1 Хлеб = 1 кг Муки + 2 Яйца)
    # Списание: Мука: 1*2=2 кг, Яйца: 2*2=4 шт.
    model.sales().add(name='Хлеб', price=200, quantity=2.0, discount=0)
    
    # Проверка списания
    final_flour = model.stock().get('Мука').quantity
    final_egg = model.stock().get('Яйцо').quantity
    
    assert model.sales().len() == 1
    assert final_flour == initial_flour - 2.0  # 10.0 - 2.0 = 8.0
    assert final_egg == initial_egg - 4.0      # 50.0 - 4.0 = 46.0
    
    # Проверка ошибки при недостатке запаса
    # Попытка продать 30 шт. "Хлеб" (нужно 30*1=30 кг Муки, есть 8.0)
    with pytest.raises(ValueError, match="Недостаточно запаса для 'Мука'. Требуется списание 30.00, текущий остаток 8.00."):
        model.sales().add(name='Хлеб', price=200, quantity=30.0, discount=0)


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
    # Мука: цена 50, кол-во 5.0 -> Расход: 50 * 5 = 250
    assert model.expenses().len() == 1
    assert model.calculate_expenses() == 250.0
    
    # Прибыль = Доход - Расход = 560 - 250 = 310
    assert model.calculate_profit() == 310.0
    
    # Добавляем еще один расход (другой тип)
    model.expense_types().add(name='Аренда', default_price=1000, category_name='Платежи')
    model.expenses().add(name='Аренда', price=1000, quantity=1.0, supplier_name=None) # Расход: 1000
    
    # Общий Расход = 250 + 1000 = 1250
    assert model.calculate_expenses() == 1250.0
    
    # Новая Прибыль = 560 - 1250 = -690
    assert model.calculate_profit() == -690.0