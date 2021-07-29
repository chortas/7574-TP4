# 7574-TP4

## Instrucciones generales 

### Script de generación del docker compose

Se corre con el comando `make docker-compose-file`. Para parametrizar la cantidad de nodos y poder escalar el sistema se requiere ver las primeras lineas del script `write_docker_compose.py` donde se explica cómo hacerlo.

### Corrida

Para que el flujo del trabajo práctico tenga sentido es necesario correr primero rabbit, luego los diversos contenedores que crean las colas y luego el cliente:

1. Correr rabbit -> `./rabbit_run.sh`.

2. Correr los contenedores que crean las colas:

- Borrar el storage por si quedó de una corrida previa: `sudo rm -rf storage`

- Levantar los contenedores: `make docker-compose-up`

3. Correr el cliente -> `./client_run.sh`

### Documentación

https://docs.google.com/document/d/1bg8r3Rn-eCd014MPBOZxOh47sCh943EmTOtXtM0OC_Q/edit?usp=sharing 
