# Backend

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

## API

Interactive docs: `http://localhost:8000/docs`

```bash
curl http://localhost:8000/openapi.json
```
