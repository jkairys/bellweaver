"""
Backward compatibility module for Bellweaver API.

DEPRECATED: This module is kept for backward compatibility only.
Please use 'bellweaver.api' instead, or run 'bellweaver api serve' from the CLI.
"""

import warnings

# Import from the new location
from bellweaver.api import create_app

# Issue deprecation warning
warnings.warn(
    "bellweaver.app is deprecated. Use 'bellweaver.api' or 'bellweaver api serve' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["create_app"]


if __name__ == "__main__":
    import os

    app = create_app()
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=5000, use_reloader=debug)
