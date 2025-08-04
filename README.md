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


git clone this repo, then:
cd raspberry
chmod +x *.py
chmod +x *.sh
because linux hates me

systemctl restart mysql

cd SolarMonitor
sudo systemctl stop solarmon.measure
chmod -x raspberry/*.py
chmod -x raspberry/*.sh
git pull origin main
chmod +x raspberry/*.py
chmod +x raspberry/*.sh
sudo systemctl start solarmon.measure


