@echo off
title Hydra Frontend - Vite
cd /d "%~dp0\frontend"
echo ========================================================
echo        HYDRA DECISION SUPPORT - FRONTEND SERVICE
echo ========================================================
call npm.cmd run dev
pause

