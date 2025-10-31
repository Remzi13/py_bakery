import pytest
import uuid
from datetime import datetime
from model import model
from model.entities import Category, Unit, unit_by_name, Ingredient, Product
import xml.etree.ElementTree as ET


# --- Фикстуры для настройки тестов ---

@pytest.fixture
def model_instance():    
    return model.Model()

@pytest.fixture
def initial_setup(model_instance):
    """Фикстура для настройки базовых ингредиентов и продукта."""
    model_instance.ingredients().add("Мука", "кг")
    model_instance.ingredients().add("Сахар", "грамм")

    # Добавляем начальное количество инвентаря
    model_instance.update_inventory("Мука", 10)
    model_instance.update_inventory("Сахар", 500)

    # Добавляем тип расхода для оборудования
    model_instance.add_expense_type("Аренда", 5000, Category.ENVIRONMENT)

    # Продукт: торт (1 кг муки, 100 грамм сахара)
    ingredients = [
        {'name': "Мука", 'quantity': 1},
        {'name': "Сахар", 'quantity': 100}
    ]
    model_instance.products().add("Торт", 1500, ingredients)
    return model_instance

# --- Тесты для внутренних классов (UUID, repr, getters) ---

def test_ingredient_creation():
    """Тестирование инициализации Ingredient и геттеров."""
    name = "Яйца"
    unit = "штуки"
    ingredient = Ingredient(name, unit)
    
    assert ingredient.name == name
    assert ingredient.unit == unit
    assert isinstance(ingredient.id, uuid.UUID)

    
def test_product_creation(model_instance):
    """Тестирование инициализации Product."""
    ingredients = [{'name': "Мука", 'quantity': 1}]
    product = Product("Хлеб", 500, ingredients)
    
    assert product.name == "Хлеб"
    assert product.price == 500
    assert product.ingredients == ingredients
    assert isinstance(product.id, uuid.UUID)

def test_sale_creation_date():
    """Тестирование инициализации Sale и формата даты."""
    test_uuid = uuid.uuid4()
    sale = model.Model.Sale("Пирог", 300, 2, test_uuid, date="2025-10-28 10:30")
    
    assert sale.date == "2025-10-28 10:30"
    
    # Проверка, что при отсутствии даты генерируется строка
    sale_auto_date = model.Model.Sale("Кекс", 100, 1, test_uuid)
    # Проверка формата 'YYYY-MM-DD HH:MM'
    assert datetime.strptime(sale_auto_date.date, "%Y-%m-%d %H:%M")

# --- Тесты для основных функций model.Model ---

def test_initial_state(model_instance):
    """Тестирование начального состояния model.Model."""
    assert model_instance.ingredients().empty() == True
    assert model_instance.products().empty() == True
    assert model_instance.get_stock() == []
    assert model_instance.get_sales() == []
    assert model_instance.get_expense_types() == []
    assert model_instance.get_expenses() == []

def test_add_and_get_ingredient(model_instance):
    """Тестирование добавления ингредиента и его последствий (инвентарь, тип расхода)."""
    model_instance.ingredients().add("Молоко", unit_by_name("литр"))
    assert model_instance.ingredients().has("Молоко") == True
    # Проверка ингредиента
    milk = model_instance.ingredients().by_name("Молоко")
    assert milk is not None
    assert milk.unit == unit_by_name("литр")

    milk = model_instance.ingredients().by_id(milk.id)
    assert milk is not None
    assert milk.unit == unit_by_name("литр")
    
    # Проверка инвентаря
    stock_names = [item.name for item in model_instance.get_stock()]
    assert "Молоко" in stock_names
    milk_stock = [item for item in model_instance.get_stock() if item.name == "Молоко"][0]
    assert milk_stock.quantity == 0 # Начальное количество 0
    assert milk_stock.category == Category.INGREDIENT
    assert milk_stock.inv_id == milk.id
    
    # Проверка типа расхода
    expense_type = model_instance.get_expense_type("Молоко")
    assert expense_type is not None
    assert expense_type.default_price == 100
    assert expense_type.category == Category.INGREDIENT

def test_add_and_delete_ingredient(model_instance):
    """Тестирование добавления и удаления ингредиента."""
    model_instance.ingredients().add("Яйца", unit_by_name("штук"))
    assert model_instance.ingredients().by_name("Яйца") is not None

    model_instance.ingredients().delete("Яйца")
    assert model_instance.ingredients().by_name("Яйца") is None

def test_add_and_cant_delete_ingredient(model_instance):
    """Тестирование невозможности удаления ингредиента, если он используется в продукте."""
    model_instance.ingredients().add("Масло", unit_by_name("грамм"))
    ingredients = [{'name': "Масло", 'quantity': 50}]
    model_instance.products().add("Булочка", 200, ingredients)

    assert model_instance.products().has("Булочка") == True
    assert model_instance.products().has("Не Булочка") == False

    with pytest.raises(ValueError):
        model_instance.ingredients().delete("Масло")

def test_get_ingredients_names(initial_setup):

    names = initial_setup.ingredients().names()

    assert names[0] == "Мука"
    assert names[1] == "Сахар"


def test_ingredient_serialization_roundtrip(model_instance):
    """Тестирует сохранение и последующую загрузку списка ингредиентов."""
    
    model_instance.ingredients().add(name="Мука (Высший сорт)", unit=unit_by_name("кг"))
    model_instance.ingredients().add(name="Яйца (С0)", unit=unit_by_name("штук"))
    model_instance.ingredients().add(name="Молоко", unit=unit_by_name("литр"))

    # Создаем фиктивный корневой элемент XML
    root_element = ET.Element("data")
    model_instance.ingredients().save_to_xml(root_element)

    # 3. Загрузка (Десериализация)
    model_loader = model.Model()
    model_loader.ingredients().load_from_xml(root_element)

    # Убеждаемся, что количество загруженных элементов совпадает
    assert model_loader.ingredients().len() == model_instance.ingredients().len()
    
    # Убеждаемся, что каждый загруженный элемент совпадает с исходным
    # Поскольку Ingredient - это dataclass, сравнение объектов простое и надежное.
    assert model_loader.ingredients().data() == model_instance.ingredients().data()

def test_products_serialization_roundtrip(initial_setup):
    """Тестирует сохранение и последующую загрузку списка ингредиентов."""
    # Создаем фиктивный корневой элемент XML
    root_element = ET.Element("data")
    initial_setup.products().save_to_xml(root_element)

    # 3. Загрузка (Десериализация)
    model_loader = model.Model()
    model_loader.products().load_from_xml(root_element)

    # Убеждаемся, что количество загруженных элементов совпадает
    assert model_loader.products().len() == initial_setup.products().len()
    
    # Убеждаемся, что каждый загруженный элемент совпадает с исходным
    # Поскольку Ingredient - это dataclass, сравнение объектов простое и надежное.
    assert model_loader.products().data() == initial_setup.products().data()

def test_add_and_get_product(initial_setup):
    """Тестирование добавления продукта и геттеров."""
    products = initial_setup.products()    
    assert products.by_name("Торт").name == "Торт"
    assert "Торт" in products.names()
    assert products.by_name("Не Торт") is None

def test_delete_product(initial_setup):
    """Тестирование удаления продукта."""
    assert initial_setup.products().empty() == False
    initial_setup.products().delete("Торт")
    assert initial_setup.products().empty() == True

def test_update_inventory(initial_setup):
    """Тестирование обновления инвентаря."""
    initial_setup.update_inventory("Мука", 5) # 10 + 5 = 15
    flour_stock = [item for item in initial_setup.get_stock() if item.name == "Мука"][0]
    assert flour_stock.quantity == 15
    
    # ИСПРАВЛЕНИЕ: Замените AssertionError на KeyError
    with pytest.raises(KeyError, match="Элемент 'Вода' не найден в инвентаре"):
        initial_setup.update_inventory("Вода", 1)

def test_add_sale_and_inventory_update(initial_setup):
    """Тестирование добавления продажи и связанного обновления инвентаря."""
    
    # --- ДОБАВЛЕНИЕ НЕДОСТАЮЩЕГО ПРОДУКТА ---
    # Вам нужно убедиться, что ингредиенты 'Мука' и 'Сахар' уже добавлены!
    
    # Добавляем "Пирожок" (предполагаем, что он использует 0.5 кг Муки и 50 грамм Сахара)
    initial_setup.products().add(
        name="Пирожок", 
        price=100, # Цена продажи 100
        ingredients=[
            {'name': 'Мука', 'quantity': 0.5},
            {'name': 'Сахар', 'quantity': 50}
        ]
    )
    # ----------------------------------------
    
    # Теперь этот вызов должен работать:
    initial_setup.add_sale("Пирожок", 100, 1) 
    
    # ... (дальнейшая проверка, если есть) ...
    
    # Если строка с "Пирожок" должна была тестировать ошибку "Продукт не найден",
    # то удалите этот вызов и убедитесь, что вы тестируете продукт, который 
    # *действительно* не существует:
    with pytest.raises(ValueError, match="Продукт 'НЕ СУЩЕСТВУЮЩИЙ ПРОДУКТ' не найден"):
        initial_setup.add_sale("НЕ СУЩЕСТВУЮЩИЙ ПРОДУКТ", 1, 1)

def test_add_and_get_expense_type(initial_setup):
    """Тестирование добавления, получения и удаления типа расхода."""
    # "Аренда" уже добавлена в initial_setup
    expense_type = initial_setup.get_expense_type("Аренда")
    assert expense_type.name == "Аренда"
    assert expense_type.default_price == 5000
    assert expense_type.category == Category.ENVIRONMENT
    assert isinstance(expense_type.id, uuid.UUID)

    initial_setup.delete_expense_type("Аренда")
    assert initial_setup.get_expense_type("Аренда") is None

def test_add_expense(initial_setup):
    """Тестирование добавления расхода."""
    initial_setup.add_expense("Аренда", 5000, 1) # 1 месяц аренды
    
    expenses = initial_setup.get_expenses()
    assert len(expenses) == 1
    assert expenses[0].name == "Аренда"
    assert expenses[0].price == 5000
    assert expenses[0].quantity == 1
    assert expenses[0].category == Category.ENVIRONMENT
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