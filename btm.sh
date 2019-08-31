#!/bin/bash

if pidof -o %PPID -x "btm.sh"; then
  echo "BatchToneMapping already running, exit..."
  exit 1
fi

python main.py