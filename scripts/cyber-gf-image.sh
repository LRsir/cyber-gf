#!/usr/bin/env bash
# Ultra-simple image generator for cyber girlfriend
# Usage: ./cyber-gf-image.sh "prompt in English"
set -e
cd /home/hongcaisen/.hermes/profiles/cybergf/skills/image-api
set -a
source /home/hongcaisen/.hermes/profiles/cybergf/.env
set +a
exec python3 scripts/image_api.py --json --size 1024x1024 --quality low --format png --moderation low "$1"
