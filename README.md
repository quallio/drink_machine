# drink_machine
This is a repo for our Final Project code. It is a funny drink machine.

# Activate venv
source venv/bin/activate

# Run the DB in the Docker
docker ps
docker start drinks_postgres
docker ps (to check if it is running...)

# Run the FastApi server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Crear el venv e instalar el requirements.txt
cd drink_machine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# falla de pyspicopg
sudo apt update
sudo apt install -y python3-dev libpq-dev gcc

pip install psycopg2

pip install -r requirements.txt

Para verificar que se instaló bien: 
pip list | grep psycopg2

# También recordar crear el .env
DATABASE_URL=postgresql+asyncpg://pf:pf@192.168.1.44:5432/drinksdb

:-)



# Run the FE from frontend folder
python3 -m http.server 8080

# Check using the browser if it is running.
http://localhost:8000/docs

# Para correr el FRONTEND:
Ingresar a la carpeta "frontend" y allí ejecutar:
python3 -m http.server 8080


# Insomnia
Usa Insomnia para pegarle a los distintos endpoints.

# Conectarme desde mi notebook a la Raspberry
ssh pf@192.168.1.44
password: pf

# Como iniciar POSTGRESQL, iniciarlo así:
sudo systemctl start postgresql
# Ver si ha iniciado, así:
sudo systemctl status postgresql
# Prueba conectarte a la base de datos desde la Raspberry con (usando user "pf", con password: "pf"):
psql -U pf -d drinksdb 
# La db se llama drinksdb y ahí tenemos todas las tablas.
# para salir de escribir queries en psql desde consola: 
\q
# Para conectarme a la db de la Raspberry desde mi notebook, correr en la terminal de linux:
psql -U pf -h 192.168.1.44 -d drinksdb
# Para conectarme desde mi notebook a la Raspberry, usando el server de FastApi, revisar que el .env le pegue a la db de la Raspberry...
DATABASE_URL=postgresql+asyncpg://pf:pf@192.168.1.44:5432/drinksdb

# Ejemplo de como poner los ingredientes en el FE:
{"ron": 30, "limón": 20, "azúcar": 10}

# Para servir el FE ejecutar en /frontend :
python3 -m http.server 8080
Y abrir en el navegador : http://127.0.0.1:8080/

# BASE DE DATOS, CREACIÓN DE TABLA Y DEMAS, DESDE LAS QUERIES:

docker run -d \
  --name drinks_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=drinksdb \
  -p 5432:5432 \
  postgres:latest

--------------

CREATE TABLE drinks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

INSERT INTO drinks (name, description, ingredients)
VALUES 
('Caipirinha', 'A refreshing Brazilian cocktail.'),
('Margarita', 'A classic cocktail with tequila.');


SELECT * FROM drinks;

##############

Body Json para crear un DRINK nuevo:

	{
		"name": "Margarita new",
		"description": "Pepe A classic cocktail with tequila."
	}




ALTER TABLE drinks DROP COLUMN IF EXISTS ingredients;


Crear la tabla ingredients (Lista de ingredientes posibles)

CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_alcoholic BOOLEAN NOT NULL DEFAULT FALSE
);


Ejemplo:

INSERT INTO ingredients (name, is_alcoholic) VALUES 
('Tequila', TRUE),
('Vodka', TRUE),
('Ron', TRUE),
('Jugo de Naranja', FALSE),
('Granadina', FALSE),
('Jugo de Limón', FALSE);


Crear la tabla drink_ingredients (Relación entre tragos e ingredientes)

CREATE TABLE drink_ingredients (
    id SERIAL PRIMARY KEY,
    drink_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    amount_ml INT NOT NULL, 
    FOREIGN KEY (drink_id) REFERENCES drinks(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
);

Ejemplo de inserción de datos (asociando ingredientes a tragos):

INSERT INTO drink_ingredients (drink_id, ingredient_id, amount_ml) VALUES 
(1, 1, 50),  -- Margarita: 50ml Tequila
(1, 6, 30),  -- Margarita: 30ml Jugo de Limón
(2, 1, 40),  -- Tequila Sunrise: 40ml Tequila
(2, 4, 100), -- Tequila Sunrise: 100ml Jugo de Naranja
(2, 5, 10);  -- Tequila Sunrise: 10ml Granadina


Crear la tabla pumps (Asignación de ingredientes a las bombas)

CREATE TABLE pumps (
    id SERIAL PRIMARY KEY,      -- ID de la bomba (1-4)
    ingredient_id INT UNIQUE,   -- Ingrediente asignado a la bomba
    assigned_at TIMESTAMP DEFAULT now(),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE SET NULL
);


Ejemplo de inserción de datos:

INSERT INTO pumps (ingredient_id) VALUES 
(1),  -- Bomba 1: Tequila
(4),  -- Bomba 2: Jugo de Naranja
(5),  -- Bomba 3: Granadina
(6);  -- Bomba 4: Jugo de Limón


Consulta las tablas con:

SELECT * FROM ingredients;
SELECT * FROM drink_ingredients;
SELECT * FROM pumps;


# Para agregar un DRINK desde el FrontEnd debes llenar así la parte de INGREDIENTS:
[
    {"ingredient_id": 3, "amount_ml": 1001},  
    {"ingredient_id": 4, "amount_ml": 1122}
]

por ejemplo...



# Para abrir una pestaña del FE en la Raspberry , desde consola:

chromium-browser --noerrdialogs --disable-infobars --kiosk http://localhost:8080

