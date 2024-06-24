#!/bin/bash
set -e

session_dir="/app"
init_script="/app/init_session.py"

# Check if sessions need to be initialized
if [ ! -f "$session_dir/ytdl-main.session" ]; then
    echo "=== First run: Session initialization required ==="
    echo "Follow the prompts to create your session files."
    echo ""
    python3 "$init_script"
    echo ""
fi

exec python3 main.py
