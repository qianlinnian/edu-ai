@echo off
cd /d %~dp0\..
set PYTHONPATH=%CD%
alembic upgrade head
