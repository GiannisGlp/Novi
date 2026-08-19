# Novi Mac Brain Documentation

This directory contains the Mac Brain architecture, implementation documentation, model compatibility notes, scenarios, and evidence guidance.

The executable Python implementation lives separately in `mac_brain/`. The separation is intentional because macOS commonly uses a case-insensitive filesystem and cannot safely materialize both `MAC_BRAIN` and `mac_brain` as distinct directories.
