import pytest
import uuid
from datetime import datetime
from model import model # Предполагается, что ваш класс Model находится в model.py

# --- Фикстуры для настройки тестов ---

@pytest.fixture
def model_instance():    
    return model.Model()

@pytest.fixture
def initial_setup(model_instance):
    """Фикстура для настройки базовых ингредиентов и продукта."""
    model_instance.add_ingredient("Мука", "кг")
    model_instance.add_ingredient("Сахар", "грамм")

    # Добавляем начальное количество инвентаря
    model_instance.update_inventory("Мука", 10)
    model_instance.update_inventory("Сахар", 500)

    # Добавляем тип расхода для оборудования
    model_instance.add_expense_type("Аренда", 5000, model.Model.Category.ENVIROMENT)

    # Продукт: торт (1 кг муки, 100 грамм сахара)
    ingredients = [
        {'name': "Мука", 'quantity': 1},
        {'name': "Сахар", 'quantity': 100}
    ]
    model_instance.add_product("Торт", 1500, ingredients)
    return model_instance

# --- Тесты для внутренних классов (UUID, repr, getters) ---

def test_ingredient_creation():
    """Тестирование инициализации Ingredient и геттеров."""
    name = "Яйца"
    unit = "штуки"
    ingredient = model.Model.Ingredient(name, unit)
    
    assert ingredient.name() == name
    assert ingredient.unit() == unit
    assert isinstance(ingredient.id(), uuid.UUID)

    # Тестирование repr
    assert repr(ingredient).startswith("Ingredient(id=")
    assert f"name='{name}'" in repr(ingredient)
    
def test_product_creation(model_instance):
    """Тестирование инициализации Product."""
    ingredients = [{'name': "Мука", 'quantity': 1}]
    product = model.Model.Product("Хлеб", 500, ingredients)
    
    assert product.name() == "Хлеб"
    assert product.price() == 500
    assert product.ingredients() == ingredients
    assert isinstance(product.id(), uuid.UUID)

def test_sale_creation_date():
    """Тестирование инициализации Sale и формата даты."""
    test_uuid = uuid.uuid4()
    sale = model.Model.Sale("Пирог", 300, 2, test_uuid, date="2025-10-28 10:30")
    
    assert sale.date() == "2025-10-28 10:30"
    
    # Проверка, что при отсутствии даты генерируется строка
    sale_auto_date = model.Model.Sale("Кекс", 100, 1, test_uuid)
    # Проверка формата 'YYYY-MM-DD HH:MM'
    assert datetime.strptime(sale_auto_date.date(), "%Y-%m-%d %H:%M")

# --- Тесты для основных функций model.Model ---

def test_initial_state(model_instance):
    """Тестирование начального состояния model.Model."""
    assert model_instance.get_ingredients() == []
    assert model_instance.get_products() == []
    assert model_instance.get_stock() == []
    assert model_instance.get_sales() == []
    assert model_instance.get_expense_types() == []
    assert model_instance.get_expenses() == []

def test_add_and_get_ingredient(model_instance):
    """Тестирование добавления ингредиента и его последствий (инвентарь, тип расхода)."""
    model_instance.add_ingredient("Молоко", "литр")
    
    # Проверка ингредиента
    milk = model_instance.get_ingredient("Молоко")
    assert milk is not None
    assert milk.unit() == "литр"
    
    # Проверка инвентаря
    stock_names = [item.name() for item in model_instance.get_stock()]
    assert "Молоко" in stock_names
    milk_stock = [item for item in model_instance.get_stock() if item.name() == "Молоко"][0]
    assert milk_stock.quantity() == 0 # Начальное количество 0
    assert milk_stock.category() == model.Model.Category.INGREDIENT
    assert milk_stock.inv_id() == milk.id()
    
    # Проверка типа расхода
    expense_type = model_instance.get_expense_type("Молоко")
    assert expense_type is not None
    assert expense_type.default_price() == 100
    assert expense_type.category() == model.Model.Category.INGREDIENT

def test_add_and_get_product(initial_setup):
    """Тестирование добавления продукта и геттеров."""
    products = initial_setup.get_products()
    assert len(products) == 1
    assert products[0].name() == "Торт"
    assert initial_setup.get_product_by_name("Торт") == products[0]
    assert "Торт" in initial_setup.get_products_names()
    assert initial_setup.get_product_by_name("Не Торт") is None

def test_delete_product(initial_setup):
    """Тестирование удаления продукта."""
    initial_setup.delete_product("Торт")
    assert initial_setup.get_products() == []

def test_update_inventory(initial_setup):
    """Тестирование обновления инвентаря."""
    initial_setup.update_inventory("Мука", 5) # 10 + 5 = 15
    flour_stock = [item for item in initial_setup.get_stock() if item.name() == "Мука"][0]
    assert flour_stock.quantity() == 15

    # Тестирование assert False при отсутствии элемента
    with pytest.raises(AssertionError, match="Элемент не найден в инвентаре"):
        initial_setup.update_inventory("Вода", 1)

def test_add_sale_and_inventory_update(initial_setup):
    """Тестирование добавления продажи и связанного обновления инвентаря."""
    initial_flour = initial_setup.get_stock()[0].quantity() # 10 кг
    initial_sugar = initial_setup.get_stock()[1].quantity() # 500 грамм

    # Продаем 2 торта (2 * 1 кг муки, 2 * 100 грамм сахара)
    initial_setup.add_sale("Торт", 1500, 2)
    
    sales = initial_setup.get_sales()
    assert len(sales) == 1
    assert sales[0].product_name() == "Торт"
    assert sales[0].quantity() == 2

    # Проверка инвентаря после продажи
    flour_stock = [item for item in initial_setup.get_stock() if item.name() == "Мука"][0]
    sugar_stock = [item for item in initial_setup.get_stock() if item.name() == "Сахар"][0]

    assert flour_stock.quantity() == initial_flour - 2 # 10 - 2 = 8
    assert sugar_stock.quantity() == initial_sugar - 200 # 500 - 200 = 300

    # Продажа несуществующего продукта
    with pytest.raises(AssertionError, match="Продукт не найден"):
        initial_setup.add_sale("Пирожок", 100, 1)

def test_add_and_get_expense_type(initial_setup):
    """Тестирование добавления, получения и удаления типа расхода."""
    # "Аренда" уже добавлена в initial_setup
    expense_type = initial_setup.get_expense_type("Аренда")
    assert expense_type.name() == "Аренда"
    assert expense_type.default_price() == 5000
    assert expense_type.category() == model.Model.Category.ENVIROMENT
    assert isinstance(expense_type.id(), uuid.UUID)

    initial_setup.delete_expense_type("Аренда")
    assert initial_setup.get_expense_type("Аренда") is None

def test_add_expense(initial_setup):
    """Тестирование добавления расхода."""
    initial_setup.add_expense("Аренда", 5000, 1) # 1 месяц аренды
    
    expenses = initial_setup.get_expenses()
    assert len(expenses) == 1
    assert expenses[0].name() == "Аренда"
    assert expenses[0].price() == 5000
    assert expenses[0].quantity() == 1
    assert expenses[0].category() == model.Model.Category.ENVIROMENT
    # Проверка формата даты, аналогично Sale

def test_calculate_finance(initial_setup):
    """Тестирование расчета дохода, расхода и прибыли."""
    # Продажи
    initial_setup.add_sale("Торт", 1500, 2)
    initial_setup.add_sale("Торт", 1500, 1) 
    
    # Расходы
    initial_setup.add_expense("Аренда", 5000, 1) 
    initial_setup.add_expense("Мука", 120, 5) 

    income = initial_setup.calculate_income()
    expenses = initial_setup.calculate_expenses()
    profit = initial_setup.calculate_profit()

    # ----------------------------

    assert income == 4500
    assert expenses == 5600 
    assert profit == -1100