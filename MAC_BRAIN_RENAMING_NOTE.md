# macOS case-collision fix

The repository contains both `MAC_BRAIN` (documentation) and `mac_brain` (Python implementation). macOS case-insensitive filesystems can materialize these as one directory and break `import mac_brain`.

The documentation directory is being renamed to `MAC_BRAIN_DOCS` so the executable Python package `mac_brain` has an unambiguous filesystem path on macOS.
