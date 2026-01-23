# BUGS
* expenses documents    
    * unit не должны редактироваться    
* нет копки add order
* не работает перезагрузка страницы по f5
* stock 
    * можно добавлять stock item с отрицательными занчения     

# TODO
* добавить SoftDelete
* для продуктов надо добавить категории (Regular, Drink, Special)
* в suppliers добавить поле комментарии 
* dashboard
    * total revenu -> month revenu
    * добавить month expenses 
* в расходах при изменения на складе делаются в две транзакции
* добавить сборку под PyInstaller
* сделать миграцию баз данных 
* создать таблицу clients и добавить в orders


# REFACTORING
* надо упростить api/routers/products.py
* добавить поле низкий запас в stock item