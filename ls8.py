#!/usr/bin/env python3

"""Main."""

import sys
# ⬇️ unresolved inport? --> cpu ⬇️
from cpu import *

# ⬇️ undefined variable? --> CPU() ⬇️
cpu = CPU()

cpu.load()
cpu.run()