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
mkdir -p "$HOME/.config/newsboat"
mkdir -p "$HOME/.tmux/status"
mkdir -p "$HOME/.tmux/plugins"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.summarize"

cp "$repo_dir/wezterm/wezterm.lua" "$HOME/.config/wezterm/wezterm.lua"
cp "$repo_dir/wezterm/assets/cyberpunk-red.jpg" "$HOME/.config/wezterm/assets/cyberpunk-red.jpg"

cp "$repo_dir/tmux/tmux.conf" "$HOME/.tmux.conf"
cp "$repo_dir/tmux/status/"*.sh "$HOME/.tmux/status/"
chmod +x "$HOME/.tmux/status/"*.sh

cp "$repo_dir/newsboat/config" "$HOME/.config/newsboat/config"
cp "$repo_dir/newsboat/urls" "$HOME/.config/newsboat/urls"

cp "$repo_dir/summarize/summarize" "$HOME/.local/bin/summarize"
chmod +x "$HOME/.local/bin/summarize"
cp "$repo_dir/summarize/config.json" "$HOME/.summarize/config.json"

# Put ~/.local/bin ahead of the rest of PATH so the summarize wrapper
# intercepts the real CLI. Idempotent: the line is appended to ~/.zprofile once.
zprofile="$HOME/.zprofile"
path_line='export PATH="$HOME/.local/bin:$PATH"'
if ! grep -qsF "$path_line" "$zprofile"; then
  printf '\n# Added by WezTerm-Setup install.sh\n%s\n' "$path_line" >> "$zprofile"
  echo "Added ~/.local/bin to PATH in ~/.zprofile."
fi

# Install the upstream @steipete/summarize CLI if it is missing, and point the
# wrapper at it via SUMMARIZE_REAL_BIN when it is not at the default location.
if command -v npm >/dev/null 2>&1; then
  real_summarize="$(npm prefix -g)/bin/summarize"
  if [[ ! -x "$real_summarize" && ! -x /usr/local/bin/summarize ]]; then
    echo "Installing @steipete/summarize globally..."
    npm install -g @steipete/summarize \
      || echo "warning: @steipete/summarize install failed; install it manually." >&2
  fi
  if [[ -x "$real_summarize" && "$real_summarize" != /usr/local/bin/summarize ]]; then
    real_line="export SUMMARIZE_REAL_BIN=\"$real_summarize\""
    if ! grep -qsF "$real_line" "$zprofile"; then
      printf '%s\n' "$real_line" >> "$zprofile"
      echo "Set SUMMARIZE_REAL_BIN -> $real_summarize in ~/.zprofile."
    fi
  fi
else
  echo "warning: npm not found; skipping @steipete/summarize install." >&2
fi

# Add a fastfetch greeting to ~/.zshrc. Idempotent: appended only once.
if ! grep -qsF "fastfetch greeting" "$HOME/.zshrc"; then
  cat >> "$HOME/.zshrc" <<'ZSHRC'

# fastfetch greeting — shown once per terminal tab (skips extra tmux split panes)
if command -v fastfetch >/dev/null; then
  if [[ -n "$TMUX" ]]; then
    if ! tmux show-environment FASTFETCH_GREETED &>/dev/null; then
      fastfetch
      tmux set-environment FASTFETCH_GREETED 1
    fi
  else
    fastfetch
  fi
fi
ZSHRC
  echo "Added fastfetch greeting to ~/.zshrc."
fi

if [[ ! -d "$HOME/.tmux/plugins/tpm" ]]; then
  git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
fi

"$HOME/.tmux/plugins/tpm/bin/install_plugins" || true

echo "WezTerm + tmux setup installed."
echo "Open WezTerm to start a tmux-backed terminal."
