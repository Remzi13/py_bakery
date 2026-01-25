# BUGS
* expenses documents    
    * unit не должны редактироваться    
* не работает перезагрузка страницы по f5
* stock 
    * можно добавлять stock item с отрицательными занчения
* dashboard
    * не работает кнопка "Add sale"


# TODO
* в suppliers добавить поле комментарии 
* dashboard
    * total revenu -> month revenu
    * добавить month expenses 
* в расходах при изменения на складе делаются в две транзакции
* создать таблицу clients и добавить в orders
* в форме Add order надо заменить галочку completed на проверку даты, если дата меньше текущей, заказ готов
* в таблицу с заказами надо добавить скидку 

# FEATURES
* добавить SoftDelete
* для продуктов надо добавить категории (Regular, Drink, Special)
* добавить сборку под PyInstaller
* сделать миграцию баз данных 

# REFACTORING
* надо упростить api/routers/products.py
* добавить поле низкий запас в stock item
* вынести константы default_units

# IDEAS
* добавить github actions для запуска тестов

# TO THINK
* если на складе недостаточно продуктов, то списание продукции не пройдёт 