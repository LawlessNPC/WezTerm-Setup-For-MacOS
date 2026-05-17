<div align="center">

# WezTerm Setup

<img src="wezterm/assets/cyberpunk-red.jpg" alt="Cyberpunk red terminal background" width="100%">

<br>

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-111111?style=for-the-badge&logo=apple&logoColor=white)
![WezTerm](https://img.shields.io/badge/WezTerm-GPU%20Terminal-02d7f2?style=for-the-badge)
![tmux](https://img.shields.io/badge/tmux-Powerline%20Status-00ff9c?style=for-the-badge)
![Homebrew](https://img.shields.io/badge/Homebrew-One%20Command-fcee0a?style=for-the-badge&logo=homebrew&logoColor=111111)

A neon macOS terminal setup that installs WezTerm, tmux, fonts, and a privacy-safe status line in one pass.

</div>

## Why This Exists

Fresh laptops should not start with a blank terminal and a pile of forgotten dotfiles.

This repo turns a new Mac into the same terminal environment every time: a polished WezTerm window, a tmux session on launch, readable Nerd Font glyphs, a custom Powerline-style status bar, and screen-share-friendly labels that avoid exposing your real username or hostname.

## What You Get

- A dark cyberpunk-neon WezTerm theme with cyan, magenta, yellow, and green accents.
- A cinematic background image tuned with a dark readability wash.
- VictorMono Nerd Font plus Symbols Nerd Font fallback for clean Powerline rendering.
- WezTerm launching straight into tmux so the terminal always has panes, sessions, and status.
- A visible WezTerm `+` tab button: left-click opens a new tab, right-click renames the active tab.
- A custom tmux status line with current mode, repo/directory context, disk space, load, window count, pane count, date, and 12-hour time.
- Privacy-safe screen sharing: no raw username, hostname, or home-folder basename in the tmux status line.
- Newsboat, a terminal RSS reader, preconfigured with a matching neon theme, vim-style keys, and a curated feed list. The Hacker News feed uses the official RSS feed, and tmux tears down unattached sessions so closing a WezTerm tab does not leave Newsboat running in the background.
- A guarded `summarize` wrapper around the `@steipete/summarize` CLI. It resolves Hacker News item links to the source article, blocks Gemini, and limits automatic LLM choices to Claude and Codex.
- A repeatable installer for setting up another MacBook Pro from scratch.

## Install On A Fresh Mac

First install Apple's command line tools:

```sh
xcode-select --install
```

If macOS asks you to accept the license:

```sh
sudo xcodebuild -license accept
```

Then install the setup:

```sh
git clone https://github.com/LawlessNPC/WezTerm-Setup.git ~/WezTerm-Setup
cd ~/WezTerm-Setup
./install.sh
```

Open WezTerm when the installer finishes. New windows and tabs will start inside tmux automatically.

## The Status Line

The tmux bar is built to be useful at a glance without leaking personal machine details.

| Segment | Meaning |
| --- | --- |
| `TMUX` | Static privacy-safe session label |
| `Mode: Normal` | Current tmux mode |
| `Mode: Prefix` | You pressed `Ctrl-a` and tmux is waiting for the next key |
| `Mode: Copy` | tmux copy mode is active |
| `Mode: Zoom` | Current pane is zoomed |
| `Current Dir: Home` | Privacy-safe home directory display |
| `Repo: app  Branch: main` | Git repo context when available |
| `HD 3% 567Gi free` | Root disk usage and remaining space |
| `LOAD 2.25` | 1-minute system load average |
| `Windows: 1  Panes: 2` | tmux window and pane count |
| `Sun 17 May  03:24 PM` | Date and 12-hour time |

## Keyboard Flow

Prefix key:

```text
Ctrl-a
```

Common bindings:

| Keys | Action |
| --- | --- |
| `Ctrl-a |` | Split pane horizontally |
| `Ctrl-a -` | Split pane vertically |
| `Ctrl-a h/j/k/l` | Resize panes |
| `Ctrl-a m` | Zoom current pane |
| `Ctrl-a r` | Reload `~/.tmux.conf` |
| `v` in copy mode | Start selection |
| `y` in copy mode | Copy selection to the macOS clipboard |
| Mouse drag | Select and copy straight to the macOS clipboard |

## WezTerm Tab Controls

The WezTerm tab bar always stays visible and includes the `+` tab button.

| Action | Result |
| --- | --- |
| Left-click `+` | Open a new tmux-backed WezTerm tab |
| Right-click `+` | Prompt to rename the active WezTerm tab |
| Submit a blank tab name | Reset the active tab title |

## Summarize Guard

`install.sh` installs the `summarize` wrapper to `~/.local/bin/summarize`, prepends `~/.local/bin` to your `PATH` in `~/.zprofile`, and `npm install -g`s the upstream `@steipete/summarize` CLI if it is missing.

It keeps the upstream `@steipete/summarize` CLI available while adding local policy:

- Hacker News item URLs such as `https://news.ycombinator.com/item?id=...` are resolved to the linked story before summarizing.
- Gemini CLI/API usage is refused, even if a command explicitly passes a Gemini model.
- Auto model selection uses only `cli/claude/sonnet` and `cli/codex/gpt-5.2`.
- The default summary length is `short`, which avoids the upstream CLI returning raw extracted text for shorter pages.

The wrapper runs the real `@steipete/summarize` binary found via `SUMMARIZE_REAL_BIN`, or `/usr/local/bin/summarize` by default. When the CLI installs elsewhere (such as Homebrew's `/opt/homebrew/bin`), `install.sh` writes the correct `SUMMARIZE_REAL_BIN` into `~/.zprofile` automatically.

## Installed Pieces

Homebrew installs:

```text
git
micro
newsboat
node
tmux
fastfetch
wezterm
font-victor-mono-nerd-font
font-symbols-only-nerd-font
```

Config installed:

```text
~/.config/wezterm/wezterm.lua
~/.config/wezterm/assets/cyberpunk-red.jpg
~/.tmux.conf
~/.tmux/status/context.sh
~/.tmux/status/disk.sh
~/.tmux/status/load.sh
~/.config/newsboat/config
~/.config/newsboat/urls
~/.local/bin/summarize
~/.summarize/config.json
```

`install.sh` also appends (never overwrites) to `~/.zprofile`, putting `~/.local/bin` on `PATH` for the `summarize` wrapper.

tmux plugins are managed by TPM. The installer clones TPM and runs the plugin installer.

## Repository Layout

```text
.
|-- Brewfile
|-- install.sh
|-- newsboat
|   |-- config
|   `-- urls
|-- summarize
|   |-- config.json
|   `-- summarize
|-- tmux
|   |-- tmux.conf
|   `-- status
|       |-- context.sh
|       |-- disk.sh
|       `-- load.sh
`-- wezterm
    |-- wezterm.lua
    `-- assets
        `-- cyberpunk-red.jpg
```

## Manual Install

Use this if you want to copy the config files yourself:

```sh
mkdir -p ~/.config/wezterm/assets ~/.config/newsboat ~/.tmux/status ~/.local/bin ~/.summarize
cp wezterm/wezterm.lua ~/.config/wezterm/wezterm.lua
cp wezterm/assets/cyberpunk-red.jpg ~/.config/wezterm/assets/cyberpunk-red.jpg
cp tmux/tmux.conf ~/.tmux.conf
cp tmux/status/*.sh ~/.tmux/status/
chmod +x ~/.tmux/status/*.sh
cp newsboat/config ~/.config/newsboat/config
cp newsboat/urls ~/.config/newsboat/urls
cp summarize/summarize ~/.local/bin/summarize
chmod +x ~/.local/bin/summarize
cp summarize/config.json ~/.summarize/config.json
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile
npm install -g @steipete/summarize
```

Install TPM:

```sh
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
~/.tmux/plugins/tpm/bin/install_plugins
```

## Troubleshooting

### Git or Homebrew says the Xcode license is not accepted

Run:

```sh
sudo xcodebuild -license accept
```

### Powerline arrows look broken

Make sure the Nerd Font casks installed successfully, then restart WezTerm:

```sh
brew install --cask font-victor-mono-nerd-font font-symbols-only-nerd-font
```

### WezTerm opens but tmux does not start

Check that tmux is installed:

```sh
command -v tmux
```

If it is missing:

```sh
brew install tmux
```

### Newsboat says another instance is already running

This setup sets `destroy-unattached on` in tmux. Reload the config in any active tmux session:

```sh
tmux source-file ~/.tmux.conf
```

After that, closing a WezTerm tab should destroy its tmux session and stop foreground programs like Newsboat.

### `summarize` tries to use Gemini

The wrapper blocks Gemini at the command level and the config removes Gemini from auto selection. Check that the wrapper is first in `PATH`:

```sh
which -a summarize
```

The first result should be:

```text
~/.local/bin/summarize
```

## Keep This Backup Updated

After changing your local WezTerm or tmux setup, copy the updated files into this repo and push:

```sh
cd ~/WezTerm-Setup
git add .
git commit -m "Update terminal setup"
git push
```
