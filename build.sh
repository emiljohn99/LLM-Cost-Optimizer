#!/usr/bin/env bash
set -e
pip install -r requirements.txt
python data/build_db.py
python classifier/train.py