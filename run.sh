#!/bin/bash

# Kick off all servers
python3 server.py Goloman &
python3 server.py Hands &
python3 server.py Holiday &
python3 server.py Welsh &
python3 server.py Wilkes

pkill python3
