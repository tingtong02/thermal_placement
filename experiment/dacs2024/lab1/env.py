# setup environment variables

import os
import sys

CLDSE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(CLDSE_ROOT)

LAB1_ROOT = os.path.join(CLDSE_ROOT, 'experiment/dacs2024/lab1')

RESULT_DIR = os.path.join(LAB1_ROOT, 'results')

ASAP7_ROOT = os.environ.get('ASAP7_HOME', '/home/lisihang/asap7')

GENUS_BIN = os.environ.get('GENUS_BIN', '/opt/eda/Cadence_DDI_23.14/bin/genus')

INNOVUS_BIN = os.environ.get('INNOVUS_BIN', '/opt/eda/Cadence_DDI_23.14/bin/innovus')

