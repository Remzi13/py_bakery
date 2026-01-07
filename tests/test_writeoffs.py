import pytest 

from tests.core import SQLiteModel, model, conn

@pytest.fixture
def write_off_data(model: SQLiteModel):
    """
    Настраивает минимальные данные для тестов списаний: 
    Ингредиент 'Мука' (Materials) и Продукт 'Круассан' (с рецептом).
    Использует фикстуру model (SQLiteModel) для доступа к репозиториям.
    """
    
    # 1. Materials/Запас (Мука)
    # model.ingredients().add() создает запись в ingredients, stock и expense_types
    model.ingredients().add(name="Мука", unit_name="kg")
    # Устанавливаем начальный запас: 10 кг
    model.stock().set("Мука", 10.0) 
    
    # 2. Продукт (Круассан) с рецептом: 0.1 кг муки на 1 шт.
    croissant = model.products().add(
        name="Круассан", 
        price=150, 
        ingredients=[{'name':"Мука", 'quantity': 0.1}] # <-- Важный рецепт для логики списания
    )
    
    # Получаем ID продукта для проверки записей в таблице списаний
    croissant_id = model.products().by_name("Круассан").id
    
    return {
        "croissant_id": croissant_id,
        "croissant_name": "Круассан",
        "flour_name": "Мука",
        "model": model # Возвращаем модель для удобства доступа в тестах
    }


class TestWriteOffsRepository:
   
    def test_add_write_off_product_success(self, write_off_data: dict):
        """Проверяет успешное списание готового продукта (УМЕНЬШАЕТ Stock ингредиентов)."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        flour_name = write_off_data['flour_name']
        croissant_name = write_off_data['croissant_name']
        
        initial_flour_stock = model.stock().get(flour_name).quantity # 10.0 кг
        write_off_qty = 5.0 # Списываем 5 круассанов
        
        # Ожидаемое списание: 5 * 0.1 кг = 0.5 кг муки
        expected_flour_decrease = write_off_qty * 0.1 
        
        w_repo.add(
            item_name=croissant_name,
            item_type="product",
            quantity=write_off_qty,
            reason="Просрочка"
        )
        
        # 1. Проверяем, что запас МУКИ уменьшился
        final_flour_stock = model.stock().get(flour_name).quantity
        assert final_flour_stock == initial_flour_stock - expected_flour_decrease
        assert final_flour_stock == 9.5
        
        # 2. Проверяем, что запись о списании продукта создана
        assert w_repo.len() == 1
        write_off_record = w_repo.data()[0]
        assert write_off_record.product_id == write_off_data['croissant_id']
        assert write_off_record.stock_item_id is None # Списывается продукт, а не StockItem
        assert write_off_record.quantity == write_off_qty

    def test_add_write_off_stock_success(self, write_off_data: dict):
        """Проверяет успешное списание сырья (уменьшение Stock)."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        flour_name = write_off_data['flour_name']
        initial_stock = model.stock().get(flour_name).quantity # 10.0
        write_off_qty = 2.5 
        
        w_repo.add(
            item_name=flour_name,
            item_type="stock",
            quantity=write_off_qty,
            reason="Испорчено влагой"
        )
        
        # 1. Проверяем, что запас уменьшился
        final_stock = model.stock().get(flour_name).quantity
        assert final_stock == initial_stock - write_off_qty
        
        # 2. Проверяем, что запись о списании создана (product_id должен быть None)
        assert w_repo.len() == 1
        write_off_record = w_repo.data()[0]
        assert write_off_record.product_id is None
        # Проверяем, что stock_item_id ЗАПОЛНЕН для сырья
        assert write_off_record.stock_item_id == model.stock().get(flour_name).id
        assert write_off_record.quantity == write_off_qty

    # =================================================================
    # ТЕСТЫ НА ОШИБКИ СПИСАНИЯ
    # =================================================================
    
    def test_write_off_insufficient_product_stock(self, write_off_data: dict):
        """
        Проверяет ошибку при попытке списать продукт, на производство которого
        не хватает ингредиентов.
        """
        model = write_off_data['model']
        w_repo = model.writeoffs()
        flour_name = write_off_data['flour_name']
        
        # Текущий запас муки: 10.0 кг. Рецепт: 0.1 кг/шт.
        # Для 101 круассана нужно 101 * 0.1 = 10.1 кг.
        write_off_qty = 101.0 
        
        initial_stock = model.stock().get(flour_name).quantity 

        # Ожидаем ошибку ValueError
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=write_off_data['croissant_name'],
                item_type="product",
                quantity=write_off_qty,
                reason="Тест нехватки продукта"
            )
        
        # Проверяем, что запас НЕ изменился (откат транзакции)
        final_stock = model.stock().get(flour_name).quantity
        assert final_stock == initial_stock
        
        # Проверяем, что запись о списании НЕ создана
        assert w_repo.len() == 0
        assert "Не хватает ингредиента" in str(excinfo.value)
        
    
    def test_write_off_insufficient_stock(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать больше сырья, чем есть на складе."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        flour_name = write_off_data['flour_name']
        
        initial_stock = model.stock().get(flour_name).quantity # 10.0
        write_off_qty = 15.0 
        
        # Ожидаем ошибку ValueError
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=flour_name,
                item_type="stock",
                quantity=write_off_qty,
                reason="Нехватка сырья"
            )
        
        # Проверяем, что запас не изменился (откат транзакции)
        final_stock = model.stock().get(flour_name).quantity
        assert final_stock == initial_stock
        
        # Проверяем, что запись о списании НЕ создана
        assert w_repo.len() == 0
        assert "Недостаточно запаса" in str(excinfo.value)


    def test_write_off_non_existent_item_product(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать несуществующий продукт."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name="Торт Наполеон",
                item_type="product",
                quantity=1.0,
                reason="Ошибка инвентаризации"
            )
        
        assert w_repo.len() == 0
        assert "не найден в списке продуктов" in str(excinfo.value)
        
    def test_write_off_non_existent_item_stock(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать несуществующее Materials/запас."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name="Новый Ингредиент",
                item_type="stock",
                quantity=1.0,
                reason="Ошибка инвентаризации"
            )
        
        assert w_repo.len() == 0
        assert "не найден на складе для списания" in str(excinfo.value)


    def test_write_off_invalid_item_type(self, write_off_data: dict):
        """Проверяет ошибку при недопустимом типе элемента."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=write_off_data['flour_name'],
                item_type="equipment", # Недопустимый тип
                quantity=1.0,
                reason="Тест"
            )
        
        assert w_repo.len() == 0
        assert "Недопустимый тип элемента" in str(excinfo.value)

    def test_write_off_non_positive_quantity(self, write_off_data: dict):
        """Проверяет ошибку при попытке списать нулевое или отрицательное количество."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        with pytest.raises(ValueError) as excinfo:
            w_repo.add(
                item_name=write_off_data['croissant_name'],
                item_type="product",
                quantity=0.0,
                reason="Тест"
            )
        
        assert w_repo.len() == 0
        assert "Количество для списания должно быть положительным" in str(excinfo.value)
        
    # =================================================================
    # ТЕСТЫ НА МЕТОДЫ ПОЛУЧЕНИЯ ДАННЫХ
    # =================================================================

    def test_data_and_len(self, write_off_data: dict):
        """Проверяет получение списка списаний и их количества."""
        model = write_off_data['model']
        w_repo = model.writeoffs()
        
        # Списание продукта (уменьшает ингредиенты, регистрирует продукт)
        w_repo.add("Круассан", "product", 2.0, "Тест 2")
        # Списание сырья (уменьшает Materials, регистрирует Materials)

        #time.sleep(6)

        w_repo.add("Мука", "stock", 1.0, "Тест 1")

        assert w_repo.len() == 2
        
        all_write_offs = w_repo.data()
        assert len(all_write_offs) == 2
        
        # Проверяем, что первый элемент (самый новый, т.к. ORDER BY date DESC) - это Мука
        assert all_write_offs[1].quantity == 1.0
        assert all_write_offs[1].product_id is None # Мука - Materials, product_id пуст
        
        # Проверяем, что второй элемент - это Круассан
        assert all_write_offs[0].quantity == 2.0
        assert all_write_offs[0].product_id == write_off_data['croissant_id'] # Круассан - продукт, product_id заполнен
