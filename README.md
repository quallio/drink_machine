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

# Check using the browser if it is running.
http://localhost:8000/docs

# Insomnia
Usa Insomnia para pegarle a los distintos endpoints.

# Conectarme desde mi notebook a la Raspberry

ssh pf@192.168.1.44
password: pf

# Como iniciado POSTGRESQL, iniciarlo así:
sudo systemctl start postgresql

# Ver si ha iniciado, así:
sudo systemctl status postgresql

# Entrar a POSTGRESQL:
sudo -u postgres psql

# para salir de escribir queries en psql desde consola: 
\q

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
    description TEXT,
    ingredients JSONB NOT NULL
);

INSERT INTO drinks (name, description, ingredients)
VALUES 
('Caipirinha', 'A refreshing Brazilian cocktail.', '{"cachaça": 50, "lime": 30, "sugar": 20}'),
('Margarita', 'A classic cocktail with tequila.', '{"tequila": 50, "lime": 30, "triple sec": 20}');


SELECT * FROM drinks;

##############

Body Json para crear un DRINK nuevo:

	{
		"name": "Margarita new",
		"description": "Pepe A classic cocktail with tequila.",
		"ingredients": {
			"lime": 3022,
			"tequila": 52120,
			"triple sec": 2033
		}
	}




