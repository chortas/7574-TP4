docker network create -d bridge 7574-tp4_default
docker build -t "rabbitmq:latest" rabbitmq
docker run -p 15672:15672 -p 5672:5672  --name rabbitmq --network=7574-tp4_default rabbitmq:latest
