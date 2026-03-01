#!/usr/bin/env bash
# Render build script — installs Python deps + Playwright browsers

set -e

pip install -r requirements.txt
playwright install --with-deps chromium
