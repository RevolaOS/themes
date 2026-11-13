# SPDX-License-Identifier: GPL-3.0-only
"""The one error the toolchain raises for bad input."""


def fail(where: str, message: str):
    """Raise a ValueError that names where in the input the problem is."""
    raise ValueError(f"{where}: {message}" if where else message)
