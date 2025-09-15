#!/bin/sh
set -e

# Ensure all required media directories exist with proper permissions
mkdir -p /app/media/uploads/user
chmod -R 755 /app/media

# Execute the command passed to the entrypoint
exec "$@"
