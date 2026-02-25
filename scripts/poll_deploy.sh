#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/axtft/projects/axtft"
BRANCH="main"
SERVICE_NAME="axtft-api.service"

cd "$APP_DIR"

LOCAL="$(git rev-parse HEAD)"
git fetch origin "$BRANCH"
REMOTE="$(git rev-parse origin/$BRANCH)"

if [ "$LOCAL" != "$REMOTE" ]; then
  git reset --hard "origin/$BRANCH"
  git clean -fd
  sudo systemctl restart "$SERVICE_NAME"
fi