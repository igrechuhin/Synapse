#!/usr/bin/env python3
"""Function-length check for JavaScript (currently a no-op).

JavaScript/TypeScript function parsing is toolchain-specific and not yet wired
into Synapse for this repository. This entrypoint exists to satisfy the
language-router contract and can be upgraded to a real implementation later.
"""

from __future__ import annotations

import sys


def main() -> None:
    print("✅ JavaScript function-length check not implemented (skipped)")
    sys.exit(0)


if __name__ == "__main__":
    main()
