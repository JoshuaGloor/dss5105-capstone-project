@echo off
setlocal
cd /d "%~dp0.."
set "UV_CACHE_DIR=%CD%\.cache\uv"
set "PYTHONUTF8=1"
uv run python -m dss5105.evaluator_demo %*
exit /b %ERRORLEVEL%
