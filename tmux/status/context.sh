#!/usr/bin/env sh

path=${1:-$PWD}
home=${HOME%/}

if root=$(git -C "$path" rev-parse --show-toplevel 2>/dev/null); then
  repo=$(basename "$root")
  branch=$(git -C "$path" branch --show-current 2>/dev/null)
  if [ -z "$branch" ]; then
    branch=$(git -C "$path" rev-parse --short HEAD 2>/dev/null)
  fi

  if [ -n "$branch" ]; then
    printf 'Repo: %s  Branch: %s\n' "$repo" "$branch"
  else
    printf 'Repo: %s\n' "$repo"
  fi
  exit 0
fi

case "${path%/}" in
  "$home")
    printf 'Current Dir: Home\n'
    ;;
  "$home"/*)
    printf 'Current Dir: %s\n' "$(basename "$path")"
    ;;
  *)
    printf 'Current Dir: %s\n' "$(basename "$path")"
    ;;
esac
