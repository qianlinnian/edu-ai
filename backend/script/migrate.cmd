@echo off
cd /d %~dp0\..
set PYTHONPATH=%CD%
set DEBUG=true
alembic upgrade head
