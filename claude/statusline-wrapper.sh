#!/bin/bash
# Read JSON input once
input=$(cat)

# Get git info from existing script
git_info=$(echo "$input" | bash ~/.claude/statusline-command.sh)

# Get context percentage from ccstatusline (resolve via PATH so this works
# whether npm installed it to ~/.local/bin, /opt/homebrew/bin, etc.)
context_pct=""
if ccstatusline_bin=$(command -v ccstatusline 2>/dev/null); then
  context_pct=$(echo "$input" | "$ccstatusline_bin")
fi

# Combine outputs (skip the trailing " | " when ccstatusline is unavailable)
if [ -n "$context_pct" ]; then
  printf '%s | %s' "$git_info" "$context_pct"
else
  printf '%s' "$git_info"
fi
