#!/bin/bash

port=${PORT:-5001}
FLASK_APP=api.py flask run --port $port