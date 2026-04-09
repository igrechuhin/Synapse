#!/usr/bin/env python3
"""Build step for Python projects.

Python has no separate compilation step. Type-checking and tests serve
as the build gate and are handled by run_quality_gate(). This script
is a no-op so the CI parity discovery loop runs uniformly across all
language subfolders.
"""

import sys

print("ℹ️  Python: no compile step (type-checking runs via run_quality_gate)")
sys.exit(0)
