#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATABASE_URL="${DATABASE_URL:?DATABASE_URL is required}"
mkdir -p "$BACKUP_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
target="$BACKUP_DIR/attendance_${timestamp}.dump"

pg_dump "$DATABASE_URL" --format=custom --file="$target"
echo "Backup created: $target"
