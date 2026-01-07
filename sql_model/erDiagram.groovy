erDiagram
    %% Справочники
    units {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
    }
    stock_categories {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
    }
    expense_categories {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
    }

    %% Основные сущности
    ingredients {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
        INTEGER unit_id FK "FK (unit_id)"
    }
    products {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
        INTEGER price
    }
    stock {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
        INTEGER category_id FK "FK (category_id)"
        REAL quantity
        INTEGER unit_id FK "FK (unit_id)"
    }
    expense_types {
        INTEGER id PK "PK (id)"
        TEXT name "UNIQUE (name)"
        INTEGER default_price
        INTEGER category_id FK "FK (category_id)"
    }

    %% Связующая таблица (Многие-ко-Многим)
    product_ingredients {
        INTEGER product_id PK, FK "PK, FK (product_id)"
        INTEGER ingredient_id PK, FK "PK, FK (ingredient_id)"
        REAL quantity
    }

    %% Таблицы операций
    expenses {
        INTEGER id PK "PK (id)"
        INTEGER type_id FK "FK (type_id)"
        TEXT name
        INTEGER price
        INTEGER category_id FK "FK (category_id)"
        REAL quantity
        TEXT date
    }
    sales {
        INTEGER id PK "PK (id)"
        INTEGER product_id FK "FK (product_id)"
        TEXT product_name
        INTEGER price
        REAL quantity
        INTEGER discount
        TEXT date
    }
    writeoffs {
        INTEGER id PK "PK (id)"
        INTEGER product_id FK "FK (product_id, NULL)"
        INTEGER stock_item_id FK "FK (stock_item_id, NULL)"
        INTEGER unit_id FK "FK (unit_id, NULL)"
        REAL quantity
        TEXT reason
        TEXT date
    }

    %% Определение связей (FK)
    units ||--o{ ingredients : "unit_id"
    units ||--o{ stock : "unit_id"
    units ||--o{ writeoffs : "unit_id (optional)"

    stock_categories ||--o{ stock : "category_id"
    
    expense_categories ||--o{ expense_types : "category_id"
    expense_categories ||--o{ expenses : "category_id"

    expense_types ||--o{ expenses : "type_id"

    products ||--|{ product_ingredients : "product_id"
    ingredients ||--|{ product_ingredients : "ingredient_id"

    products ||--o{ sales : "product_id"
    products ||--o{ writeoffs : "product_id (optional)"

    stock ||--o{ writeoffs : "stock_item_id (optional)"