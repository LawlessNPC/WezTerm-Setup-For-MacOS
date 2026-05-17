#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is not installed. Installing Homebrew first."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

brew bundle --file "$repo_dir/Brewfile"

mkdir -p "$HOME/.config/wezterm/assets"
mkdir -p "$HOME/.tmux/status"
mkdir -p "$HOME/.tmux/plugins"

cp "$repo_dir/wezterm/wezterm.lua" "$HOME/.config/wezterm/wezterm.lua"
cp "$repo_dir/wezterm/assets/cyberpunk-red.jpg" "$HOME/.config/wezterm/assets/cyberpunk-red.jpg"

cp "$repo_dir/tmux/tmux.conf" "$HOME/.tmux.conf"
cp "$repo_dir/tmux/status/"*.sh "$HOME/.tmux/status/"
chmod +x "$HOME/.tmux/status/"*.sh

if [[ ! -d "$HOME/.tmux/plugins/tpm" ]]; then
  git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi

"$HOME/.tmux/plugins/tpm/bin/install_plugins" || true

echo "WezTerm + tmux setup installed."
echo "Open WezTerm to start a tmux-backed terminal."
