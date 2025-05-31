"# Energy Use App" 

cs frontend
npm run dev
http://localhost:5173/

cs raspberry
uvicorn backend:app --reload
http://localhost:8000/data works

D:\coding\SolarMonitor\raspberry>"venv\Scripts\activate.bat"
(venv) D:\coding\SolarMonitor\raspberry>pip install xxx
(venv) D:\coding\SolarMonitor\raspberry>pip freeze > requirements.txt
venv\Scripts\deactivate


Remember to revert bind-address = 0.0.0.0 in /etc/mysql/mariadb.conf.d/50-server.cnf
