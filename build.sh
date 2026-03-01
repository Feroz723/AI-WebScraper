#!/usr/bin/env bash
# Render build script — installs Python deps + Playwright Chromium

set -e

pip install -r requirements.txt

# Install Chromium browser only (no system deps — Render already has them)
python -m playwright install chromium
