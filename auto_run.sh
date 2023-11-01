#!/bin/sh
cd /home/code

#gunicorn
gunicorn main:app --workers 4 --timeout 300 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:3132 --reload

# uvicorn
#uvicorn main:app --host 0.0.0.0 --port 2290 --reload
