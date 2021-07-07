docker build -t "client:latest" .
docker run -p 3000:3000 --network=7574-tp2_default client:latest
