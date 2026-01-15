import pytest

from tests.core import SQLiteModel, model, conn

@pytest.fixture
def supplier_data(model: SQLiteModel):
    """Предоставляет инициализированный репозиторий поставщиков с тестовыми данными."""
    s_repo = model.suppliers()
    s_repo.add(name="Мука и Зерно", contact_person="Иванов И.И.", phone="555-1234")
    s_repo.add(name="Дрожжи и Добавки", contact_person="Петров П.П.")
    
    # ID для тестов
    supplier1_id = s_repo.by_name("Мука и Зерно").id
    supplier2_id = s_repo.by_name("Дрожжи и Добавки").id
    
    return {
        'model': model,
        'repo': s_repo,
        'id1': supplier1_id,
        'id2': supplier2_id
    }

class TestSuppliersRepository:
    """Тесты для репозитория SuppliersRepository."""

    def test_add_supplier(self, model: SQLiteModel):
        """Проверяет корректное добавление нового поставщика."""
        repo = model.suppliers()
        
        # Добавляем нового поставщика с полными данными
        supplier = repo.add(
            name="Пекарское Equipment", 
            contact_person="Анна Смирнова", 
            phone="89101112233", 
            email="anna@equipment.com", 
            address="г. Москва, ул. Пекарская, 5"
        )
        
        assert supplier.id is not None
        assert supplier.name == "Пекарское Equipment"
        assert supplier.contact_person == "Анна Смирнова"
        assert supplier.phone == "89101112233"
        assert supplier.email == "anna@equipment.com"
        assert supplier.address == "г. Москва, ул. Пекарская, 5"
        assert repo.len() == 1

    def test_add_duplicate_supplier_raises_error(self, model: SQLiteModel):
        """Проверяет, что добавление поставщика с существующим именем вызывает ошибку."""
        repo = model.suppliers()
        repo.add("Тестовый Поставщик", phone="1")
        
        with pytest.raises(ValueError) as excinfo:
            repo.add("Тестовый Поставщик", phone="2") # Повтор
            
        assert "уже существует" in str(excinfo.value)
        assert repo.len() == 1 # Проверяем, что дубликат не был добавлен

    def test_get_by_id_and_by_name(self, model: SQLiteModel):
        """Проверяет получение поставщика по ID и по имени."""
        repo = model.suppliers()
        
        # Добавляем поставщика и запоминаем ID
        supplier_added = repo.add("Молокозавод 'Свежий'", "Олег")
        
        # Получение по ID
        supplier_by_id = repo.by_id(supplier_added.id)
        assert supplier_by_id is not None
        assert supplier_by_id.name == "Молокозавод 'Свежий'"
        
        # Получение по имени
        supplier_by_name = repo.by_name("Молокозавод 'Свежий'")
        assert supplier_by_name is not None
        assert supplier_by_name.id == supplier_added.id
        
        # Тест на несуществующего
        assert repo.by_id(999) is None
        assert repo.by_name("Несуществующий") is None

    def test_data_and_names(self, model: SQLiteModel):
        """Проверяет получение списка всех поставщиков и списка только их имен."""
        repo = model.suppliers()
        
        repo.add("Поставщик A", "A")
        repo.add("Поставщик B", "B")
        repo.add("Поставщик C", "C")
        
        # Проверка data()
        all_suppliers = repo.data()
        assert len(all_suppliers) == 3
        # Проверяем сортировку по имени
        assert all_suppliers[0].name == "Поставщик A"
        
        # Проверка names()
        all_names = repo.names()
        assert all_names == ["Поставщик A", "Поставщик B", "Поставщик C"]
        
    def test_delete_supplier(self, model: SQLiteModel):
        """Проверяет удаление поставщика по имени."""
        repo = model.suppliers()
        repo.add("Удаляемый Поставщик")
        repo.add("Остающийся Поставщик")
        
        assert repo.len() == 2
        
        # Удаляем
        repo.delete("Удаляемый Поставщик")
        
        assert repo.len() == 1
        assert repo.by_name("Удаляемый Поставщик") is None
        assert repo.by_name("Остающийся Поставщик") is not None
        
        # Удаление несуществующего не вызывает ошибку
        repo.delete("Несуществующий")
        assert repo.len() == 1

    def test_delete_by_id(self, model: SQLiteModel):
        """Проверяет удаление поставщика по ID."""
        repo = model.suppliers()
        s1 = repo.add("S1")
        s2 = repo.add("S2")
        
        assert repo.len() == 2
        repo.delete_by_id(s1.id)
        assert repo.len() == 1
        assert repo.by_id(s1.id) is None
        assert repo.by_id(s2.id) is not None

    def test_search(self, model: SQLiteModel):
        """Проверяет поиск поставщиков."""
        repo = model.suppliers()
        repo.add("Alpha", contact_person="John", email="john@alpha.com")
        repo.add("Beta", contact_person="Jane", phone="123456")
        repo.add("Gamma", address="Main St")
        
        # Поиск по имени
        assert len(repo.search("Alpha")) == 1
        # Поиск по контакту
        assert len(repo.search("Jane")) == 1
        # Поиск по частичному совпадению
        assert len(repo.search("a")) == 3 # Alpha, Beta, Gamma all contain 'a' (case-insensitive usually in SQLite)
        # Если SQLite case-sensitive, то 'Alpha' might not match 'a' depending on collation.
        # But usually LIKE is case-insensitive for ASCII.
        
        # Поиск по телефону
        assert len(repo.search("123")) == 1
        
        # Пустой поиск
        assert len(repo.search("Nothing")) == 0

    def test_update_all_fields(self, supplier_data: dict):
        """Проверяет успешное обновление всех полей поставщика."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id1']
        
        # Обновляем все поля
        updated_supplier = s_repo.update(
            supplier_id=supplier_id,
            name="Новая Мука",
            contact_person="Сидоров С.С.",
            phone="999-0001",
            email="sidorov@new.com",
            address="ул. Обновленная, 10"
        )
        
        # Проверяем, что объект обновлен
        assert updated_supplier.name == "Новая Мука"
        assert updated_supplier.contact_person == "Сидоров С.С."
        assert updated_supplier.phone == "999-0001"
        assert updated_supplier.email == "sidorov@new.com"
        assert updated_supplier.address == "ул. Обновленная, 10"
        
        # Проверяем, что данные в БД корректны
        db_supplier = s_repo.by_id(supplier_id)
        assert db_supplier.name == "Новая Мука"


    def test_update_only_name(self, supplier_data: dict):
        """Проверяет обновление только имени, остальные поля должны сохраниться/обнулиться."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id2'] # ID поставщика "Дрожжи и Добавки"
        
        # --- ИСПРАВЛЕНИЕ: Получаем оригинальный объект для частичного обновления ---
        original_supplier = s_repo.by_id(supplier_id)
        
        # Обновляем только имя. Для сохранения контактных данных передаем их обратно.
        updated_supplier = s_repo.update(
            supplier_id=supplier_id,
            name="Новые Дрожжи",
            # Передаем оригинальные значения, чтобы они не были обнулены
            contact_person=original_supplier.contact_person, 
            phone=original_supplier.phone,
            email=original_supplier.email,
            address=original_supplier.address
        )
        
        assert updated_supplier.name == "Новые Дрожжи"
        # Проверка, что оригинальное значение сохранилось
        assert updated_supplier.contact_person == "Петров П.П." 
        assert updated_supplier.phone is None 
        assert updated_supplier.email is None 
        assert updated_supplier.address is None
        
    def test_update_non_existent_supplier(self, supplier_data: dict):
        """Проверяет ошибку при попытке обновить несуществующий ID."""
        s_repo = supplier_data['repo']
        
        with pytest.raises(ValueError) as excinfo:
            s_repo.update(
                supplier_id=99999,
                name="Фантомный поставщик"
            )
        
        assert "Поставщик с ID 99999 не найден" in str(excinfo.value)

    def test_update_duplicate_name(self, supplier_data: dict):
        """Проверяет ошибку IntegrityError при попытке установить дублирующееся имя."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id2'] # ID "Дрожжи и Добавки"
        
        # Пытаемся переименовать в имя первого поставщика
        with pytest.raises(ValueError) as excinfo:
            s_repo.update(
                supplier_id=supplier_id,
                name="Мука и Зерно" # Имя уже занято
            )
        
        assert "Поставщик с именем 'Мука и Зерно' уже существует" in str(excinfo.value)
        
    def test_delete_used_supplier(self, supplier_data: dict, model: SQLiteModel):
        """Проверяет ошибку при попытке удалить поставщика, связанного с расходами."""
        s_repo = supplier_data['repo']
        supplier_id = supplier_data['id1'] # ID поставщика "Мука и Зерно"
        supplier_name = "Мука и Зерно"

        # 1. Добавляем тип расхода (например, "Закупка муки")
        # Для простоты, ExpenseType не привязывается напрямую к Supplier,
        # поэтому мы сразу создаем расход.
        
        # NOTE: В ExpensesRepository.add() нет параметра supplier_id,
        # поэтому для теста мы должны выполнить прямой SQL запрос,
        # чтобы связать расход с поставщиком. 
        # Если вы хотите использовать add(), нужно его изменить.
        
        # Создаем документ, привязанный к поставщику
        model.expense_documents().add(
             date="2025-10-01 10:00",
             supplier_id=supplier_id,
             total_amount=1000,
             comment="Test",
             items=[]
        )
        model._conn.commit()
        model._conn.commit()

        # 2. Пытаемся удалить поставщика
        with pytest.raises(ValueError) as excinfo:
            s_repo.delete(supplier_name)
        
        assert f"Поставщик '{supplier_name}' связан с существующими расходами. Удаление невозможно." in str(excinfo.value)
        
        # Проверяем, что поставщик остался
        assert s_repo.by_name(supplier_name) is not None