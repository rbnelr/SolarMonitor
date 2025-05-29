"# Energy Use App" 

cs frontend
npm run dev

cs backend
uvicorn app.main:app --reload

D:\coding\SolarMonitor\raspberry>"venv\Scripts\activate.bat"
(venv) D:\coding\SolarMonitor\raspberry>pip install xxx
(venv) D:\coding\SolarMonitor\raspberry>pip freeze > requirements.txt
venv\Scripts\deactivate


Remember to revert bind-address = 0.0.0.0 in /etc/mysql/mariadb.conf.d/50-server.cnf
