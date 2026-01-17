#!/bin/bash
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --log-level info
