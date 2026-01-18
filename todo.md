# BUGS
* expenses documents
    * непоисходит списание со stock
    * expenses documents unit наду уменьшить     
    * добавить обшую цену к модальному окну     
* add product возвращает 307 Temporary Redirect неоткрывает модальное окно
* "POST /api/stock HTTP/1.1" 307 Temporary Redirect (add)
* "POST /api/suppliers HTTP/1.1" 307 Temporary Redirect (add)
* нет копки add order
* delete для products должен принимать id, а не name
* не работает перезагрузка страницы по f5

# TODO
* починить перевод на русский
* в suppliers добавить поле комментарии 
* dashboard
    * total revenu -> month revenu
    * добавить month expenses 

# REFACTORING
* переделать базу данных на sqlalchemy
