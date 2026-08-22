#!/usr/bin/env bash
cd "$(dirname "$0")"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
