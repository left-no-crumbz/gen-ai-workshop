# Gen AI Workshop

This guide shows how to set up and use a Python virtual environment for this codebase.

## Prerequisites
- Python 3.10+ installed and available on your PATH
- `pip` (ships with Python)

## Setup (Windows PowerShell)
1. **Create virtual environment**
   ```pwsh
   python -m venv .venv
   ```
2. **Activate it**
   ```pwsh
   .venv\Scripts\Activate.ps1
   ```
3. **Upgrade `pip` (recommended)**
   ```pwsh
   python -m pip install --upgrade pip
   ```
4. **Install dependencies**
   ```pwsh
   pip install -r requirements.txt
   ```

## Using the environment
- Start a new shell and activate: `.venv\Scripts\Activate.ps1`
- Deactivate when done: `deactivate`

## Environment variables
- Copy the sample file and edit values as needed:
  ```pwsh
  copy env.example .env
  ```

## Running the apps
There are multiple app parts. From an activated environment:
```pwsh
python app_part1.py
python app_part2.py
python app_part3.py
```

## Colab Links
Part 1
https://colab.research.google.com/drive/1pYfhNRaQ7D3n4KbXvwxyKGhx8k9XfT3F?usp=sharing

Part 2
https://colab.research.google.com/drive/11BCqYFpSoIGnS33TrvGaunNKD3RWoPIz?usp=sharing

Part 3
https://colab.research.google.com/drive/1HaaybqRbY21TS4n80XcaX2P_d3YfSeUW?usp=sharing
## Troubleshooting
- If activation fails, ensure PowerShell execution policy allows scripts (e.g., `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`).
- If you change dependencies, regenerate `requirements.txt` with `pip freeze > requirements.txt` while the venv is active.
