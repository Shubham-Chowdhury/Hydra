@echo off
title Hydra Master Launcher
echo Starting Hydra Services...
start "Hydra Backend" "%~dp0run_backend.cmd"
ping 127.0.0.1 -n 3 >nul
start "Hydra Frontend" "%~dp0run_frontend.cmd"
ping 127.0.0.1 -n 4 >nul
start http://localhost:5173/
echo All services launched.
