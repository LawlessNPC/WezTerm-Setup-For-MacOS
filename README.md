# WezTerm Setup

Portable backup of my WezTerm + tmux setup for macOS.

This recreates the same terminal UI:

- WezTerm cyberpunk-neon theme with background image
- VictorMono Nerd Font + Symbols Nerd Font fallback
- WezTerm launches directly into tmux
- tmux Powerline-style bottom status bar
- privacy-safe tmux status text for screen sharing
- disk usage, load average, window/pane counts, date, and 12-hour time

## Fresh Mac Setup

Install Apple's command line tools first:

```sh
xcode-select --install
```

If macOS asks you to accept the license, run:

```sh
sudo xcodebuild -license accept
```

Then clone and run the setup:

```sh
git clone https://github.com/LawlessNPC/WezTerm-Setup.git ~/WezTerm-Setup
cd ~/WezTerm-Setup
./install.sh
```

Open WezTerm after the script finishes. New tabs and windows will start in tmux automatically.

## What Gets Installed

Homebrew packages:

- `tmux`
- `git`
- `micro`

Homebrew casks:

- `wezterm`
- `font-victor-mono-nerd-font`
- `font-symbols-only-nerd-font`

Config files:

- `~/.config/wezterm/wezterm.lua`
- `~/.config/wezterm/assets/cyberpunk-red.jpg`
- `~/.tmux.conf`
- `~/.tmux/status/context.sh`
- `~/.tmux/status/disk.sh`
- `~/.tmux/status/load.sh`

tmux plugins are managed by TPM. The installer clones TPM and runs the plugin installer.

## tmux Basics

Prefix key:

```text
Ctrl-a
```

Useful bindings:

- `Ctrl-a |` split pane horizontally
- `Ctrl-a -` split pane vertically
- `Ctrl-a h/j/k/l` resize pane
- `Ctrl-a r` reload `~/.tmux.conf`
- `Ctrl-a m` zoom the current pane

Status line labels:

- `Mode: Normal` normal tmux mode
- `Mode: Prefix` prefix key has been pressed
- `Mode: Copy` copy mode is active
- `Mode: Zoom` current pane is zoomed
- `Current Dir: Home` privacy-safe home directory display
- `Repo: name Branch: branch` git context when inside a repo
- `HD 3% 567Gi free` root disk usage and free space
- `LOAD 3.55` 1-minute system load average
- `Windows: 1 Panes: 2` tmux window and pane count

## Manual Install

If you do not want to run the installer:

```sh
mkdir -p ~/.config/wezterm/assets ~/.tmux/status
cp wezterm/wezterm.lua ~/.config/wezterm/wezterm.lua
cp wezterm/assets/cyberpunk-red.jpg ~/.config/wezterm/assets/cyberpunk-red.jpg
cp tmux/tmux.conf ~/.tmux.conf
cp tmux/status/*.sh ~/.tmux/status/
chmod +x ~/.tmux/status/*.sh
```

Install TPM:

```sh
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
~/.tmux/plugins/tpm/bin/install_plugins
```

## Push This Backup To GitHub

If this folder is not already a git repo, initialize it and push it:

```sh
cd ~/WezTerm-Setup
git init
git branch -M main
git remote add origin https://github.com/LawlessNPC/WezTerm-Setup.git
git add .
git commit -m "Add portable WezTerm and tmux setup"
git push -u origin main
```

If the remote already has commits, clone it first, copy these files into the clone, then commit and push from there.
