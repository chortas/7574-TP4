# 7574-TP4

## Instrucciones generales 

### Script de generación del docker compose

Se corre con el comando `make docker-compose-file`. Para parametrizar la cantidad de nodos y poder escalar el sistema se requiere ver las primeras lineas del script `write_docker_compose.py` donde se explica cómo hacerlo.

### Corrida

Para que el flujo del trabajo práctico tenga sentido primero es necesario levantar los contenedores que crean las colas. Para esto hay dos opciones:

- Si los containers no fueron cerrados correctamente en una ejecución previa -> `make restart`

- Caso contrario -> `make docker-compose-up`

Luego, para correr  el cliente que lee los archivos correr el siguiente comando:

- `./run.sh`
