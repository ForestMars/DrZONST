#!/bin/bash

# @TODO Why is bevaviour of nvm and npm installs divergent? (fix npm install)

# Colors
RESET="\033[0m"
GREEN="\033[32m"
YELLOW="\033[33m"
ORANGE="\033[38;5;214m"  # Orange-like color
RED="\033[31m"
BLUE="\033[34m"

# Clear the terminal and source the .zshrc to load nvm immediately if it's already installed
clear
if [[ -f "$HOME/.zshrc" ]]; then
    source "$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    source "$HOME/.bashrc"
fi

# Welcome message
echo -e "${ORANGE}Welcome to the interactive installation script for nvm, Node.js, and npm.${RESET}"
echo -e "${ORANGE}This script will first check your current environment to see if these tools are installed.${RESET}"
echo -e "${ORANGE}It will then guide you through the installation process for each package.${RESET}"

# Step 1: Checking environment
echo -e "\n${ORANGE}Checking your environment for existing installations...${RESET}"

# Function to get the latest Node.js LTS version without jq
get_latest_node_version() {
  curl -s https://nodejs.org/dist/index.json | grep -o '"version": "v[0-9]\+\.[0-9]\+\.[0-9]\+"' | head -1 | awk -F '"' '{print $4}' || echo "Unable to fetch latest version"
}

# Function to get the latest npm version
get_latest_npm_version() {
  npm show npm version 2>/dev/null || echo "Unable to fetch latest npm version"
}

# Function to get the latest nvm version
get_latest_nvm_version() {
  curl -s https://api.github.com/repos/nvm-sh/nvm/releases/latest | grep -o '"tag_name": "[^"]*' | awk -F '": "' '{print $2}' || echo "Unable to fetch latest nvm version"
}

# Check nvm
if command -v nvm >/dev/null 2>&1; then
    nvm_version=$(nvm --version)
    echo -e "nvm is already installed. Version: ${YELLOW}$nvm_version${RESET}"
else
    echo -e "nvm is not installed."
fi
latest_nvm_version=$(get_latest_nvm_version)
echo -e "Latest nvm version: ${GREEN}$latest_nvm_version${RESET}"

# Check Node.js
if command -v node >/dev/null 2>&1; then
    node_version=$(node -v)
    echo -e "Node.js is already installed. Version: ${YELLOW}$node_version${RESET}"
else
    echo -e "Node.js is not installed."
fi
latest_node_version=$(get_latest_node_version)
echo -e "Latest Node.js LTS version: ${GREEN}$latest_node_version${RESET}"

# Check npm
if command -v npm >/dev/null 2>&1; then
    npm_version=$(npm -v)
    echo -e "npm is already installed. Version: ${YELLOW}$npm_version${RESET}"
else
    echo -e "npm is not installed."
fi
latest_npm_version=$(get_latest_npm_version)
echo -e "Latest npm version: ${GREEN}$latest_npm_version${RESET}"

# Pause before proceeding
echo -e "\n${ORANGE}Review the above information. Press ${GREEN}Enter ${ORANGE}to continue with installation steps.${RESET}"
read -r

# Step 2: Installation prompts
echo -e "\n${ORANGE}Now let's go through each package (nvm, Node.js, and npm) one by one.${RESET}"
echo -e "${ORANGE}We will check if it's installed and ask you if you'd like to install or update it.${RESET}"

# Function to handle errors and user decisions
handle_error() {
    error_message=$1
    step=$2
    read -rp "${RED}Error occurred: $error_message${RESET}\nDo you want to (r)etry, (s)kip, or (a)bort the $step installation? (r/s/a): " choice
    case "$choice" in
        [Rr]* ) return 1 ;;  # Retry the current step
        [Ss]* ) return 0 ;;  # Skip to next step
        [Aa]* ) exit 1 ;;    # Abort the entire process
        * ) echo "Invalid input. Aborting installation."; exit 1 ;;
    esac
}

# Install or update nvm
# @FIXME available version has a leading 'v' which is breaking this logic. 
echo -e "\n${ORANGE}nvm Installation/Update:${RESET}"
if [[ -z "$nvm_version" || "$latest_nvm_version" != "$nvm_version" ]]; then
    echo -e "Installed version: ${YELLOW}$nvm_version${RESET}"
    echo -e "To be installed version: ${GREEN}$latest_nvm_version${RESET}"
    echo -e "Do you want to install/update nvm to version $latest_nvm_version? (${GREEN}y${RESET}/${YELLOW}n${RESET}): "
    read -rp "" install_nvm

    if [[ "$install_nvm" =~ ^[Yy]$ ]]; then
        echo -e "Installing nvm version $latest_nvm_version..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/$latest_nvm_version/install.sh | bash
        if [[ $? -ne 0 ]]; then
            if ! handle_error "Failed to install/update nvm." "nvm"; then
                echo "Skipping nvm installation."
            fi
        else
            source "$HOME/.zshrc"  # Source the .zshrc file again
            echo -e "nvm installed successfully. Installed version: $(nvm --version)"
        fi
    fi
fi

# Install or update Node.js
echo -e "\n${ORANGE}Node.js Installation/Update:${RESET}"
if [[ -z "$node_version" || "$latest_node_version" != "$node_version" ]]; then
    echo -e "Installed version: ${YELLOW}$node_version${RESET}"
    echo -e "To be installed version: ${GREEN}$latest_node_version${RESET}"
    #read -rp "Do you want to install/update Node.js to version $latest_node_version? (y/n): " install_node
    echo -e "Do you want to install/update Node to version $latest_node_version? (${GREEN}y${RESET}/${YELLOW}n${RESET}): "
    read -rp "" install_node
    if [[ "$install_node" =~ ^[Yy]$ ]]; then
        echo -e "Installing Node.js version $latest_node_version..."
        nvm install "$latest_node_version"
        if [[ $? -ne 0 ]]; then
            if ! handle_error "Failed to install/update Node.js." "Node.js"; then
                echo "Skipping Node.js installation."
            fi
        else
            nvm alias default "$latest_node_version"
            echo -e "Node.js installed successfully. Installed version: $(node -v)"
        fi
    fi
fi

# Install or update npm
if [[ -z "$latest_npm_version" ]]; then
    echo "latest_nvm_version is empty or not set."
else
    echo "latest_nvm_version is set to: $latest_npm_version"
fi

echo -e "\n${ORANGE}npm Installation/Update:${RESET}"
if [[ -z "$npm_version" || "$latest_npm_version" != "$npm_version" ]]; then
    echo -e "Installed version: ${YELLOW}$npm_version${RESET}"
    echo -e "To be installed version: ${GREEN}$latest_npm_version${RESET}"
    read -rp "Do you want to install/update npm to version $latest_npm_version? (y/n): " install_npm
    if [[ "$install_npm" =~ ^[Yy]$ ]]; then
        echo -e "Installing npm version $latest_npm_version..."
        npm install -g "npm@$latest_npm_version"
        if [[ $? -ne 0 ]]; then
            if ! handle_error "Failed to install/update npm." "npm"; then
                echo "Skipping npm installation."
            fi
        else
            echo -e "npm installed successfully. Installed version: $(npm -v)"
        fi
    fi
else
    echo -e "Installed version: ${YELLOW}$npm_version${RESET}"
    echo -e "To be installed version: ${GREEN}$latest_npm_version${RESET}"
    echo -e "Current version matches latest available. Skip...? (y/n)"
    read -rp ""
fi

# Final report
echo -e "\n${ORANGE}Installation Summary:${RESET}"
echo -e "nvm: ${YELLOW}$(nvm --version)${RESET} (latest is $latest_nvm_version)"
echo -e "Node.js: ${YELLOW}$(node -v)${RESET} (latest is $latest_node_version)"
echo -e "npm: ${YELLOW}$(npm -v)${RESET} (latest is $latest_npm_version)"

echo -e "${ORANGE}Installation process complete.${RESET}"
