start cmd /k "cd /d "D:\coding\SolarMonitor\frontend" && npm run dev"
start cmd /k "cd /d "D:\coding\SolarMonitor\raspberry" && uvicorn backend:app --reload"
start cmd /k "cd /d "D:\coding\SolarMonitor\raspberry" && python measure.py"
