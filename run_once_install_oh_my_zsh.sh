#!/bin/sh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  echo "Installing Oh My Zsh..."
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended --keep-zshrc
else
  echo "Oh My Zsh is already installed."
fi

# Install custom plugins
ZSH_CUSTOM_DIR="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
VI_MODE_DIR="$ZSH_CUSTOM_DIR/plugins/zsh-vi-mode"
if [ ! -d "$VI_MODE_DIR" ]; then
  echo "Installing zsh-vi-mode..."
  git clone https://github.com/jeffreytse/zsh-vi-mode.git "$VI_MODE_DIR"
fi
