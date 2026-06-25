# Agent Instructions for `treysaddler/dotfiles`

This file provides context and instructions for AI Agents (like GitHub Copilot) interacting with this repository.

## Project Overview
This repository contains the user's dotfiles managed by **[chezmoi](https://www.chezmoi.io/)**. It ensures consistent configuration across multiple machines (macOS, Linux, etc.).

## Chezmoi Conventions

When reading or editing files in this repository, you must understand `chezmoi`'s file naming conventions:

1.  **Prefix `dot_`**: Represents a hidden file (starting with `.`) in the home directory.
    *   *Example*: `dot_zshrc` in this repo corresponds to `~/.zshrc` on the system.
2.  **Prefix `private_`**: Indicates the file should have restricted permissions (0600).
    *   *Example*: `private_dot_ssh/config`.
3.  **Directories**: Directories in this repo correspond to directories in the home directory.
    *   *Example*: `.config/git/config` would be stored here as `dot_config/git/config`.
4.  **Templates**: Files ending in `.tmpl` are Go templates. They are processed by `chezmoi` to generate the final file. Useful for machine-specific logic (e.g., `{{ if eq .chezmoi.os "darwin" }}`).

## Workflow for Agents

### 1. Reading Configuration
Always look for the source file in this repository, not the target file in the home directory path (unless checking runtime state).
*   Correct: Read `dot_zshrc` to see Zsh settings.

### 2. Modifying Configuration
To make persistent changes to the user's environment:
1.  **Edit the source file** in this repository (e.g., append an alias to `dot_zshrc`).
2.  **Apply the changes**: `chezmoi apply`
    *   *Command*: `chezmoi apply -v` (Verbose mode is helpful to see the diff of what is changing).

### 3. Adding New Configuration
If the user asks to "save" or "track" a current config file:
*   *Command*: `chezmoi add ~/.config/someapp/config.toml`

## Repository Structure

*   `dot_zshrc`: Main Z shell configuration.
*   `private_empty_dot_bashrc`: Placeholder for Bash configuration.
*   `README.md`: Human-readable documentation.
*   `AGENTS.md`: AI-readable documentation.

## Operational Notes

1. Keep shell env sourcing guarded to avoid startup errors on machines where tools are missing.
    * Example patterns:
      * `[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"`
      * `[ -f "$HOME/google-cloud-sdk/path.zsh.inc" ] && . "$HOME/google-cloud-sdk/path.zsh.inc"`
2. If chezmoi prompts because a target file changed outside chezmoi, use non-interactive flags to avoid stalling in an interactive alternate buffer.
    * Command: `chezmoi apply --force --no-pager --no-tty ~/.bashrc`
