#!/usr/bin/env bash
# run_once_after_enable-git-hooks.sh
#
# chezmoi runs this once (and again if its contents change) after applying.
# It points this dotfiles repo's git at the versioned hooks directory so the
# pre-commit hook (config-reference drift check + secret scan) is active even
# on a fresh clone. core.hooksPath is a local git setting and does NOT travel
# with a clone, which is exactly why we (re)set it here.

set -euo pipefail

SRC="$(chezmoi source-path 2>/dev/null || echo "$HOME/.local/share/chezmoi")"

if [ -d "$SRC/.git" ] && [ -d "$SRC/scripts/git-hooks" ]; then
  current="$(git -C "$SRC" config --get core.hooksPath || true)"
  if [ "$current" != "scripts/git-hooks" ]; then
    git -C "$SRC" config core.hooksPath scripts/git-hooks
    echo "chezmoi: enabled git hooks (core.hooksPath=scripts/git-hooks) in $SRC"
  fi
fi
