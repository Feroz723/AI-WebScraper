#!/usr/bin/env bash
# Render build script — installs Python deps + Playwright Chromium

set -e

pip install -r requirements.txt

# Set browser path and install Chromium
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/playwright_browsers
python -m playwright install chromium
