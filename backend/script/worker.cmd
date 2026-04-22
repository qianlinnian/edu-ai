@echo off
cd /d %~dp0\..
set PYTHONPATH=%CD%
set DEBUG=true
celery -A workers.celery_app worker --loglevel=info -P solo -Q celery,embedding,grading
