# BUGS
* expenses documents    
    * unit не должны редактироваться    
* add product возвращает 307 Temporary Redirect неоткрывает модальное окно
* "POST /api/stock HTTP/1.1" 307 Temporary Redirect (add)
* "POST /api/suppliers HTTP/1.1" 307 Temporary Redirect (add)
* нет копки add order
* не работает перезагрузка страницы по f5

# TODO
* починить перевод на русский
* в suppliers добавить поле комментарии 
* dashboard
    * total revenu -> month revenu
    * добавить month expenses 
* в расходах при изменения на складе делаются в две транзакции

# REFACTORING
* обрашнея к элементам должно быть только через id