# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

Source-of-truth dotfiles for a macOS terminal environment: WezTerm + tmux + zsh + Neovim + Newsboat, a guarded `summarize` CLI wrapper, and Claude Code statusline/completion-sound config. `install.sh` reproduces the whole setup on a fresh Mac in one pass.

Nothing is symlinked — `install.sh` **copies** files from the repo into `~`, so the repo and live config drift unless synced. Workflow: edit in this repo, deploy (run `./install.sh` or copy the individual file), commit, push. When syncing a live dotfile back into the repo, replace `/Users/<name>/` with `$HOME/` — repo files stay `$HOME`-relative for Intel/Apple Silicon portability.

## Commands

- `./install.sh` — full idempotent deploy: Homebrew bundle, config copies, plugin clones, npm installs, `~/.zprofile` appends, jq merges into `~/.claude/settings.json`.
- `bash -n install.sh` — syntax-check after editing the installer.

There is no build, lint, or test suite.

## Architecture

**install.sh is the authoritative map of where files land.** Repo path → live path is not 1:1 (`tmux/tmux.conf` → `~/.tmux.conf`, `zsh/zshrc` → `~/.zshrc`, `claude/*.sh` → `~/.claude/`). Adding or moving a config file means updating `install.sh` *and* the hand-maintained "Installed Pieces" / "Manual Install" sections of README.md.

**Append and merge, never clobber.** install.sh appends to `~/.zprofile` behind grep guards, and merges into `~/.claude/settings.json` with jq (only `.statusLine` and `.hooks.Stop`), so unrelated user settings survive re-runs. Follow the same pattern for any new settings integration.

**summarize interception chain.** `summarize/summarize` is a policy wrapper installed to `~/.local/bin/summarize`, which install.sh puts first in PATH. It resolves Hacker News item links to the source article, hard-blocks Gemini, and restricts auto model selection, then execs the real `@steipete/summarize` binary found via `SUMMARIZE_REAL_BIN` (written to `~/.zprofile` when npm's global prefix isn't `/usr/local/bin`).

**Claude Code integration.** `claude/statusline-wrapper.sh` combines git info from `statusline-command.sh` with context output from `ccstatusline` (widget config in `ccstatusline/settings.json`, resolved via PATH). `claude/sounds/task-complete.mp3` plays from an async Stop hook (`afplay -v 0.2`) instead of TTS.

**Neovim plugins are version-pinned** via `nvim/lazy-lock.json`; commit lockfile changes deliberately.

## Conventions

- Privacy: the tmux status line must never show the real username, hostname, or home-folder basename (screen-share safe). Preserve this when touching `tmux/` or `tmux/status/*.sh`.
- Theme: dark cyberpunk-neon. Keep new UI in the existing palette — bg `#0a0a12`, magenta `#d62cff`, cyan `#02d7f2`, yellow `#fcee0a`, green `#00ff9c`.
- Commits: prefix with the component touched (`wezterm:`, `tmux:`, `claude:`, `summarize:`, `docs:`), e.g. `claude: play task-complete sound via Stop hook instead of TTS`.
