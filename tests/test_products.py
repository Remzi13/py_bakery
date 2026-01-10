from tests.core import SQLiteModel, model, conn

class TestProductsRepository:

    def test_add_and_get_recipe(self, model: SQLiteModel):
        repo = model.products()
        model.stock().add('Мука', "Materials", 50, 'kg')
        model.stock().add('Вода', "Materials", 50, 'l')

        recipe = [
            {'name': 'Мука', 'quantity': 1.5}, 
            {'name': 'Вода', 'quantity': 0.5}
        ]
        repo.add(name='Багет', price=150, materials=recipe)
        
        product = repo.by_name('Багет')
        assert product.price == 150
        
        # Проверка получения рецепта из связующей таблицы
        retrieved_recipe = repo.get_materials_for_product(product.id)
        assert len(retrieved_recipe) == 2
        assert retrieved_recipe[0]['name'] == 'Мука'
        assert retrieved_recipe[0]['quantity'] == 1.5
        
    def test_update_product_and_recipe(self, model: SQLiteModel):
        repo = model.products()
        model.stock().add('Мука', "Materials", 50, 'kg')
        model.stock().add('Соль', "Materials", 50, 'g')
        
        repo.add(name='Пирог', price=500, materials=[{'name': 'Мука', 'quantity': 1.0}])
        
        # Обновление: новая цена и новый рецепт
        new_recipe = [{'name': 'Соль', 'quantity': 5.0}]
        repo.add(name='Пирог', price=600, materials=new_recipe)
        
        updated_product = repo.by_name('Пирог')
        assert updated_product.price == 600
        
        # Проверка, что старый рецепт удален, а новый добавлен
        updated_recipe = repo.get_materials_for_product(updated_product.id)
        assert len(updated_recipe) == 1
        assert updated_recipe[0]['name'] == 'Соль'
        
    def test_delete_product(self, model: SQLiteModel):
        repo = model.products()
        repo.add(name='Кекс', price=50, materials=[])
        
        repo.delete('Кекс')
        assert repo.has('Кекс') is False

    def test_delete_cascades_to_recipes(self, model: SQLiteModel):
        """
        Проверяет, что при удалении продукта удаляются все его рецепты (записи в таблице recipes).
        """
        repo = model.products()
        conn = model._conn # Доступ к соединению для проверки
    
        # 1. Подготовка: Добавляем ингредиенты
        model.stock().add('Мука', "Materials", 50, 'kg')
    
        # 2. Добавление продукта с рецептом
        recipe = [{'name': 'Мука', 'quantity': 1.0}]
        repo.add(name='Пирог', price=500, materials=recipe)
    
        # Проверка: В таблице recipes должна быть 1 запись
        initial_recipe_count = conn.execute("SELECT COUNT(*) FROM product_stock").fetchone()[0]
        assert initial_recipe_count == 1
    
        # 3. Действие: Удаление продукта
        repo.delete('Пирог')
        assert repo.has('Пирог') is False
    
        # 4. Проверка: В таблице recipes должно быть 0 записей (Каскадное удаление сработало)
        final_recipe_count = conn.execute("SELECT COUNT(*) FROM product_stock").fetchone()[0]
        assert final_recipe_count == 0

    def test_data(self, model: SQLiteModel):
        repo = model.products()
        
        # Для добавления продукта нужны ингредиенты
        model.stock().add('Инг1', "Materials", 10, 'kg')
        
        repo.add(name='Торт', price=1000, materials=[{'name': 'Инг1', 'quantity': 1.0}])
        repo.add(name='Кекс', price=50, materials=[])
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Торт'
        assert data[1].price == 50
        assert len(data[0].materials) == 1 # Проверка, что рецепт загрузился
