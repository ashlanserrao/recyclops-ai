# recyclops-ai

A household air-quality planner for Indian cities (Prompt Wars Challenge 6: Urban Air Quality Assistant).

It turns **live, measured** pollution readings from the nearest monitoring station into a day plan for each member
of a household, with indoor actions and greener transport swaps. Each suggestion explains **why** and shows its
**impact as a number computed in code**. The AI only explains and personalises the wording; it never produces an
AQI value or a decision, and the app gives full advice without it.

> Work in progress. Full documentation (architecture, prompt design, tests, sample inputs) comes with the first release.

## Run locally

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
copy .env.example .env   # then add your keys
.\venv\Scripts\python.exe -m uvicorn recyclops.api.main:app --reload
```

Checks (what CI runs): `.\venv\Scripts\python.exe scripts\check.py`

## License

MIT
