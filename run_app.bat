@echo off
echo Starting DBT Project Explorer...

echo Starting backend server...
start cmd /k "cd %~dp0backend && python simple_app.py --projects-dir ..\sample_dbt_projects"

echo Starting frontend...
start cmd /k "cd %~dp0frontend && npm start"

echo Application started successfully!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000 