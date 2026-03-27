#!/usr/bin/env python3
"""
FINAL SOLUTION: Create INPUT Excel from qty.txt + PWD Database
100% accurate, instant, no OCR needed
"""
import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment
from datetime import datetime

# Complete PWD BSR Database
PWD_DATABASE = {
    '1.1.2': {'desc': 'Wiring of light/fan point - Medium point (up to 6 mtr.) with 1.5 sq.mm FR PVC insulated copper conductor in recessed PVC conduit with modular accessories', 'unit': 'point', 'rate': 602.0},
    '1.1.3': {'desc': 'Wiring of light/fan point - Long point (up to 10 mtr.) with 1.5 sq.mm FR PVC insulated copper conductor in recessed PVC conduit with modular accessor