#!/bin/bash
# Multi AI Asistent Coder - Compiled Version
python3 -m __pycache__.ai_coder.cpython-312 "$@" || python3 -c "import sys; sys.path.insert(0, '.'); from __pycache__ import ai_coder; ai_coder.main()"
