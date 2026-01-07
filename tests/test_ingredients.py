import pytest

from tests.core import model, SQLiteModel, conn

class TestIngredientsRepository:

    def test_add_with_relations(self, model: SQLiteModel):
        """Проверка, что добавление ингредиента создает связанные StockItem и ExpenseType."""
        repo = model.ingredients()
        
        repo.add(name='Мука', unit_name='kg')

        # 1. Проверка Ingredients
        assert repo.len() == 1
        ing = repo.by_name('Мука')
        assert ing.name == 'Мука'
        
        # 2. Проверка StockItem
        stock_item = model.stock().get('Мука')
        assert stock_item is not None
        assert stock_item.quantity == 0.0
        assert stock_item.category_id == model.stock()._get_category_id('Materials')

        # 3. Проверка ExpenseType
        expense_type = model.expense_types().get('Мука')
        assert expense_type is not None
        assert expense_type.default_price == 100
        
    def test_delete_allowed(self, model: SQLiteModel):
        repo = model.ingredients()
        repo.add(name='Соль', unit_name='kg')
        
        # Проверка, что удаление разрешено
        assert repo.can_delete('Соль') is True
        repo.delete('Соль')
        
        assert repo.has('Соль') is False
        assert model.stock().get('Соль') is None # Проверка удаления связи

    def test_delete_denied(self, model: SQLiteModel):
        repo = model.ingredients()
        repo.add(name='Сахар', unit_name='kg')
        
        # Искусственно создаем продукт, использующий Сахар, 
        # чтобы проверить запрет на удаление.
        model.products().add(
            name='Торт', 
            price=1000, 
            ingredients=[{'name': 'Сахар', 'quantity': 0.5}]
        )
        
        # Проверка, что удаление запрещено
        assert repo.can_delete('Сахар') is False
        with pytest.raises(ValueError, match="Ингредиент 'Сахар' используется в продукте"):
            repo.delete('Сахар')
        assert repo.has('Сахар') is True
        
    def test_data(self, model: SQLiteModel):
        repo = model.ingredients()
        repo.add(name='Сахар', unit_name='kg')
        repo.add(name='Вода', unit_name='l')
        
        data = repo.data()
        assert len(data) == 2
        assert data[0].name == 'Сахар'
        assert data[1].unit_id == 3 # ID 'l' (при условии, что 'l' имеет id=3)
