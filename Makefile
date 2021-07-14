SHELL := /bin/bash
PWD := $(shell pwd)

GIT_REMOTE = github.com/7574-sistemas-distribuidos/docker-compose-init

default: build

all:

deps:
	go mod tidy
	go mod vendor

build: deps
	GOOS=linux go build -o bin/client github.com/7574-sistemas-distribuidos/docker-compose-init/client
.PHONY: build


blockchain:
	docker build -f ./blockchain/Dockerfile -t "blockchain:latest" .
.PHONY: blockchain

docker-image:
	docker build -f ./filter_avg_rating_server_duration/Dockerfile -t "filter_avg_rating_server_duration:latest" .
	docker build -f ./group_by/Dockerfile -t "group_by:latest" .
	docker build -f ./reducer_group_by/Dockerfile -t "reducer_group_by:latest" .
	docker build -f ./filter_solo_winner_player/Dockerfile -t "filter_solo_winner_player:latest" .
	docker build -f ./filter_ladder_map_mirror/Dockerfile -t "filter_ladder_map_mirror:latest" .
	docker build -f ./broadcaster/Dockerfile -t "broadcaster:latest" .
	docker build -f ./players_cleaner/Dockerfile -t "players_cleaner:latest" .
	docker build -f ./filter_rating/Dockerfile -t "filter_rating:latest" .
	docker build -f ./join/Dockerfile -t "join:latest" .
	docker build -f ./reducer_join/Dockerfile -t "reducer_join:latest" .
	docker build -f ./winner_rate_calculator/Dockerfile -t "winner_rate_calculator:latest" .
	docker build -f ./top_civ_calculator/Dockerfile -t "top_civ_calculator:latest" .
	docker build -f ./interface/Dockerfile -t "interface:latest" .
	docker build -f ./monitor/Dockerfile -t "monitor:latest" .
.PHONY: docker-image

docker-compose-up: docker-image
	docker-compose -f docker-compose.yml up --build --scale filter_solo_winner_player=2
.PHONY: docker-compose-up

docker-compose-down:
	docker-compose -f docker-compose.yml stop -t 1
	docker-compose -f docker-compose.yml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker-compose -f docker-compose.yml logs -f
.PHONY: docker-compose-logs

restart:
	make docker-compose-down
	make docker-compose-up
.PHONY: restart

docker-compose-file:
	python3 writer_docker_compose.py
.PHONY: docker-compose-file
