#!/bin/bash
pip install -r requirements.txt
alembic upgrade head  # si tu utilises Alembic pour les migrations
