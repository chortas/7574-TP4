DOCKER_COMPOSE_FILE_NAME = "docker-compose.yml"

HEADER_AND_RABBIT = """version: '3'
services:
  rabbitmq:
    build:
      context: ./rabbitmq
      dockerfile: Dockerfile
    ports:
      - 15672:15672
      - 5672:5672
"""

VOLUME = """
volumes:
  storage:
"""

'''
Constantes que hay que modificar para escalar y generar el docker compose correspondiente.
Los nodos que no están incluidos en estas constantes no pueden escalarse (son nodos master) 
por el esquema de centinelas planteado.
'''

# filter_avg_rating_server_duration
N_FILTER_ARSD = 1

# reducers_group_by_match
N_REDUCERS_GROUP_BY_MATCH = 2

# reducers_rate_winner_join
N_REDUCERS_RATE_WINNER_JOIN = 2

# reducers_top_civ_join
N_REDUCERS_TOP_CIV_JOIN = 2

# reducers_group_by_civ_rate_winner
N_REDUCERS_GROUP_BY_CIV_RATE_WINNER = 2

# reducers_group_by_civ_top_civ
N_REDUCERS_GROUP_BY_CIV_TOP_CIV = 2

# filter_solo_winner_player
N_FILTER_SOLO_WINNER_PLAYER = 1

# winner_rate_calculator
N_WINNER_RATE_CALCULATOR = 1

# top_civ_calculator
N_TOP_CIV_CALCULATOR = 1

INTERFACE_IP = 'interface'

INTERNAL_PORT = 3001

N_FINAL_NODES = N_FILTER_ARSD + N_FILTER_SOLO_WINNER_PLAYER + N_WINNER_RATE_CALCULATOR + N_TOP_CIV_CALCULATOR

MONITOR_PORT = 3003

MONITOR_FREQUENCY = 3

N_MONITORS = 2

MONITOR_IPS = [f"monitor_{i}" for i in range(1, N_MONITORS+1)]

def write_constant(compose_file, constant):
    compose_file.write(constant)

def write_section(compose_file, container_name, image, env_variables, monitor = False, volume=False):
    section = f"""\n  {container_name}:
    container_name: {container_name}
    image: {image}:latest
    entrypoint: python3 /main.py
    restart: on-failure
    depends_on:
      - rabbitmq\n"""

    section_monitor = ""
    for monitor_ip in MONITOR_IPS:
      section_monitor += f"""      - {monitor_ip}\n"""
    final_section = f"""    links: 
      - rabbitmq
    environment:\n"""

    if not monitor: 
      section += section_monitor
    else:
      section += f"""    volumes: 
      - /var/run/docker.sock:/var/run/docker.sock
      - /storage:/states\n"""

    if volume:
      section += f"""    volumes: 
      - /storage:/states\n"""

    section += final_section
    
    for env, variable in env_variables.items():
      section += f"      - {env}={variable}\n"
    compose_file.write(section)

with open(DOCKER_COMPOSE_FILE_NAME, "w") as compose_file:
    write_constant(compose_file, HEADER_AND_RABBIT)
    
    # monitor
    for i in range(N_MONITORS):
      env_variables = {"INTERNAL_PORT": MONITOR_PORT, "TIMEOUT": 10, "ID": MONITOR_IPS[i]}
      write_section(compose_file, MONITOR_IPS[i], "monitor", env_variables, monitor = True)

    # filter_avg_rating_server_duration
    env_variables = {"MATCH_QUEUE": "filter_arsd_queue", "OUTPUT_QUEUE": "output_queue_1", 
    "AVG_RATING_FIELD": "average_rating", "SERVER_FIELD": "server",
    "DURATION_FIELD": "duration", "ID_FIELD": "token",
    "INTERFACE_IP": INTERFACE_IP, "INTERFACE_PORT": INTERNAL_PORT,
    "MONITOR_IPS": ",".join(MONITOR_IPS), "MONITOR_PORT": MONITOR_PORT,
    "FREQUENCY": MONITOR_FREQUENCY}
    for i in range(1, N_FILTER_ARSD+1):
      env_variables["ID"] = f"filter_avg_rating_server_duration_{i}"
      write_section(compose_file, f"filter_avg_rating_server_duration_{i}", "filter_avg_rating_server_duration", env_variables)

    '''
    # matches_broadcaster
    env_variables = {"ROW_QUEUE": "match_queue", 
    "QUEUES_TO_SEND": "filter_arsd_queue,filter_lmm_queue",
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY,
    "ID": "matches_broadcaster"}    
    write_section(compose_file, "matches_broadcaster", "broadcaster", env_variables)
    
    # group_by_match
    GROUP_BY_MATCH_QUEUE = "group_by_match_queue"
    env_variables = {"QUEUE_NAME": "group_by_player_queue", "N_REDUCERS": N_REDUCERS_GROUP_BY_MATCH, "GROUP_BY_QUEUE": GROUP_BY_MATCH_QUEUE,
    "GROUP_BY_FIELD": "match", "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
    "FREQUENCY": MONITOR_FREQUENCY, "ID": "group_by_match"}    
    write_section(compose_file, "group_by_match", "group_by", env_variables)

    # reducers_group_by_match
    for i in range(1, N_REDUCERS_GROUP_BY_MATCH+1):
      env_variables = {"GROUP_BY_QUEUE": f"{GROUP_BY_MATCH_QUEUE}_{i}", 
      "GROUP_BY_FIELD": "match", "GROUPED_PLAYERS_QUEUE": "grouped_players_queue_filter_swp", 
      "BATCH_TO_SEND": 1000, "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
      "FREQUENCY": MONITOR_FREQUENCY, "ID": f"reducer_group_by_match_{i}"}        
      write_section(compose_file, f"reducer_group_by_match_{i}", "reducer_group_by", env_variables)
    
    # filter_solo_winner_player
    env_variables = {"GROUPED_PLAYERS_QUEUE": "grouped_players_queue_filter_swp", 
    "OUTPUT_QUEUE": "output_queue_2", "RATING_FIELD": "rating", "WINNER_FIELD": "winner", 
    "INTERFACE_IP": INTERFACE_IP, "INTERFACE_PORT": INTERNAL_PORT, "MONITOR_IP": "monitor", 
    "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": f"filter_solo_winner_player_{i}"}    
    for i in range(1, N_FILTER_SOLO_WINNER_PLAYER+1):
      write_section(compose_file, f"filter_solo_winner_player_{i}", "filter_solo_winner_player", env_variables)

    # filter_ladder_map_mirror
    env_variables = {"MATCH_QUEUE": "filter_lmm_queue", 
    "MATCH_TOKEN_EXCHANGE": "match_token_exchange", 
    "TOP_CIV_ROUTING_KEY": "top_civ_routing_key", 
    "RATE_WINNER_ROUTING_KEY": "rate_winner_routing_key", "LADDER_FIELD": "ladder", 
    "MAP_FIELD": "map", "MIRROR_FIELD": "mirror", "ID_FIELD": "token",
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": "filter_ladder_map_mirror"}    
    write_section(compose_file, "filter_ladder_map_mirror", "filter_ladder_map_mirror", env_variables)

    # players_broadcaster
    env_variables = {"ROW_QUEUE": "player_queue", 
    "QUEUES_TO_SEND": "player_cleaner_queue,filter_rating_queue,group_by_player_queue",
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": "players_broadcaster"}    
    write_section(compose_file, "players_broadcaster", "broadcaster", env_variables)    
    
    # players_cleaner
    env_variables = {"PLAYER_QUEUE": "player_cleaner_queue", "MATCH_FIELD": "match", 
    "CIV_FIELD": "civ", "WINNER_FIELD": "winner", "JOIN_EXCHANGE": "match_token_exchange", 
    "JOIN_ROUTING_KEY": "player_rate_winner_routing_key", "MONITOR_IP": "monitor", 
    "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": "players_cleaner"}
    write_section(compose_file, "players_cleaner", "players_cleaner", env_variables)

    # filter_rating
    env_variables = {"PLAYER_QUEUE": "filter_rating_queue", "RATING_FIELD": "rating", "MATCH_FIELD": "match", 
    "CIV_FIELD": "civ", "ID_FIELD": "token", "JOIN_EXCHANGE": "match_token_exchange", 
    "JOIN_ROUTING_KEY": "player_top_civ_routing_key", "MONITOR_IP": "monitor", 
    "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": "filter_rating"}
    write_section(compose_file, "filter_rating", "filter_rating", env_variables)    

    # join_rate_winner
    JOIN_RATE_EXCHANGE = "join_rate_winner"
    env_variables = {"MATCH_TOKEN_EXCHANGE": "match_token_exchange", 
    "N_REDUCERS": N_REDUCERS_RATE_WINNER_JOIN, 
    "MATCH_CONSUMER_ROUTING_KEY": "rate_winner_routing_key", 
    "JOIN_EXCHANGE": JOIN_RATE_EXCHANGE, 
    "MATCH_ID_FIELD": "token", 
    "PLAYER_CONSUMER_ROUTING_KEY": "player_rate_winner_routing_key", 
    "PLAYER_MATCH_FIELD": "match", "MONITOR_IP": "monitor", 
    "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": "join_rate_winner"}
    write_section(compose_file, "join_rate_winner", "join", env_variables)    

    # join_top_civ
    JOIN_TOP_CIV_EXCHANGE = "join_top_civ"
    env_variables = {"MATCH_TOKEN_EXCHANGE": "match_token_exchange", 
    "N_REDUCERS": N_REDUCERS_TOP_CIV_JOIN, 
    "MATCH_CONSUMER_ROUTING_KEY": "top_civ_routing_key", 
    "JOIN_EXCHANGE": JOIN_TOP_CIV_EXCHANGE, "MATCH_ID_FIELD": "token", 
    "PLAYER_CONSUMER_ROUTING_KEY": "player_top_civ_routing_key", 
    "PLAYER_MATCH_FIELD": "match", "MONITOR_IP": "monitor", 
    "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
    "ID": "join_top_civ"}
    write_section(compose_file, "join_top_civ", "join", env_variables)    

    # reducers_rate_winner_join
    for i in range(1, N_REDUCERS_RATE_WINNER_JOIN+1):
      env_variables = {"JOIN_EXCHANGE": f"{JOIN_RATE_EXCHANGE}_{i}", "MATCH_CONSUMER_ROUTING_KEY": "rate_winner_routing_key",
      "PLAYER_CONSUMER_ROUTING_KEY": "player_rate_winner_routing_key", 
      "GROUPED_RESULT_QUEUE": "grouped_rate_winner_queue", "MATCH_ID_FIELD": "token", 
      "PLAYER_MATCH_FIELD": "match", "BATCH_TO_SEND": 1000, "MONITOR_IP": "monitor", 
      "MONITOR_PORT": MONITOR_PORT, "FREQUENCY": MONITOR_FREQUENCY, 
      "ID": f"reducer_rate_winner_join_{i}"}
      write_section(compose_file, f"reducer_rate_winner_join_{i}", "reducer_join", env_variables)

    # reducers_top_civ_join
    for i in range(1, N_REDUCERS_TOP_CIV_JOIN+1):
      env_variables = {"JOIN_EXCHANGE": f"{JOIN_TOP_CIV_EXCHANGE}_{i}", 
      "MATCH_CONSUMER_ROUTING_KEY": "top_civ_routing_key", 
      "PLAYER_CONSUMER_ROUTING_KEY": "player_top_civ_routing_key", 
      "GROUPED_RESULT_QUEUE": "grouped_top_civ_queue", "MATCH_ID_FIELD": "token", 
      "PLAYER_MATCH_FIELD": "match", "BATCH_TO_SEND": 1000,
      "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
      "FREQUENCY": MONITOR_FREQUENCY, "ID": f"reducer_top_civ_join_{i}"}
      write_section(compose_file, f"reducer_top_civ_join_{i}", "reducer_join", env_variables)

    # group_by_civ_rate_winner
    GROUP_BY_CIV_RATE_WINNER_QUEUE = "group_by_civ_rate_winner_queue"
    env_variables = {"QUEUE_NAME": "grouped_rate_winner_queue", 
    "N_REDUCERS": N_REDUCERS_GROUP_BY_CIV_RATE_WINNER, 
    "GROUP_BY_QUEUE": GROUP_BY_CIV_RATE_WINNER_QUEUE, "GROUP_BY_FIELD": "civ",
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
    "FREQUENCY": MONITOR_FREQUENCY, "ID": "group_by_civ_rate_winner"}
    write_section(compose_file, "group_by_civ_rate_winner", "group_by", env_variables)

    # reducers_group_by_civ_rate_winner
    for i in range(1, N_REDUCERS_GROUP_BY_CIV_RATE_WINNER+1):
      env_variables = {"GROUP_BY_QUEUE": F"{GROUP_BY_CIV_RATE_WINNER_QUEUE}_{i}",
      "GROUP_BY_FIELD": "civ", "GROUPED_PLAYERS_QUEUE": "winner_rate_calculator_queue",
      "SENTINEL_AMOUNT": N_REDUCERS_RATE_WINNER_JOIN, "BATCH_TO_SEND": 1000,
      "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
      "FREQUENCY": MONITOR_FREQUENCY, "ID": f"reducer_group_by_civ_rate_winner_{i}"}
      write_section(compose_file, f"reducer_group_by_civ_rate_winner_{i}", "reducer_group_by", env_variables)

    # group_by_civ_top_civ
    GROUP_BY_CIV_TOP_CIV_QUEUE = "group_by_civ_top_civ_queue"
    env_variables = {"QUEUE_NAME": "grouped_top_civ_queue", 
    "N_REDUCERS": N_REDUCERS_GROUP_BY_CIV_TOP_CIV,
    "GROUP_BY_QUEUE": GROUP_BY_CIV_TOP_CIV_QUEUE, "GROUP_BY_FIELD": "civ",
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
    "FREQUENCY": MONITOR_FREQUENCY, "ID": "group_by_civ_top_civ"}
    write_section(compose_file, "group_by_civ_top_civ", "group_by", env_variables)

    # reducers_group_by_civ_top_civ
    for i in range(1, N_REDUCERS_GROUP_BY_CIV_TOP_CIV+1):
      env_variables = {"GROUP_BY_QUEUE": F"{GROUP_BY_CIV_TOP_CIV_QUEUE}_{i}",
      "GROUP_BY_FIELD": "civ", "GROUPED_PLAYERS_QUEUE": "top_civ_calculator_queue",
      "SENTINEL_AMOUNT": N_REDUCERS_TOP_CIV_JOIN, "BATCH_TO_SEND": 1000,
      "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
      "FREQUENCY": MONITOR_FREQUENCY, "ID": f"reducer_group_by_civ_top_civ_{i}"}
      write_section(compose_file, f"reducer_group_by_civ_top_civ_{i}", "reducer_group_by", env_variables)

    # winner_rate_calculator
    env_variables = {"GROUPED_PLAYERS_QUEUE": "winner_rate_calculator_queue", 
    "OUTPUT_QUEUE": "output_queue_3", "WINNER_FIELD": "winner", 
    "SENTINEL_AMOUNT": N_REDUCERS_GROUP_BY_CIV_RATE_WINNER,
    "INTERFACE_IP": INTERFACE_IP, "INTERFACE_PORT": INTERNAL_PORT,
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
    "FREQUENCY": MONITOR_FREQUENCY}
    for i in range(1, N_WINNER_RATE_CALCULATOR+1):
      env_variables["ID"] = f"winner_rate_calculator_{i}"
      write_section(compose_file, f"winner_rate_calculator_{i}", "winner_rate_calculator", env_variables, volume=True)

    # top_civ_calculator
    env_variables = {"GROUPED_PLAYERS_QUEUE": "top_civ_calculator_queue", 
    "OUTPUT_QUEUE": "output_queue_4", "ID_FIELD": "token", 
    "SENTINEL_AMOUNT": N_REDUCERS_GROUP_BY_CIV_TOP_CIV,
    "INTERFACE_IP": INTERFACE_IP, "INTERFACE_PORT": INTERNAL_PORT,
    "MONITOR_IP": "monitor", "MONITOR_PORT": MONITOR_PORT, 
    "FREQUENCY": MONITOR_FREQUENCY}
    for i in range(1, N_TOP_CIV_CALCULATOR+1):
      env_variables["ID"] = f"top_civ_calculator_{i}"
      write_section(compose_file, f"top_civ_calculator_{i}", "top_civ_calculator", env_variables)
    '''

    # interface
    env_variables = {"API_PORT": 3002, "SENTINEL_AMOUNT": N_FINAL_NODES, 
    "INTERNAL_PORT": INTERNAL_PORT, "MONITOR_IPS": ",".join(MONITOR_IPS), "MONITOR_PORT": MONITOR_PORT, 
    "FREQUENCY": MONITOR_FREQUENCY, "ID": "interface"}
    write_section(compose_file, "interface", "interface", env_variables)
    
    write_constant(compose_file, VOLUME)
