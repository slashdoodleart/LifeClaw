#!/usr/bin/env bash
# LifeClaw — Single-script installer for macOS, Linux, and WSL
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  _     _  __       ____ _"
echo " | |   (_)/ _| ___ / ___| | __ ___      __"
echo " | |   | | |_ / _ \ |   | |/ _\` \ \ /\ / /"
echo " | |___| |  _|  __/ |___| | (_| |\ V  V /"
echo " |_____|_|_|  \___|\____|_|\__,_| \_/\_/"
echo -e "${NC}"
echo -e "${BOLD}LifeClaw Installer${NC}"
echo ""

# Check Python
if command -v python3 &>/dev/null; then
    PY=$(python3 --version 2>&1)
    echo -e "${GREEN}✓${NC} Python: $PY"
else
    echo -e "${RED}✗${NC} Python 3.11+ required. Install from https://python.org"
    exit 1
fi

# Check Python version >= 3.11
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
    echo -e "${RED}✗${NC} Python 3.11+ required (found $PY_VER)"
    exit 1
fi

# Check Node (optional, for web dashboard)
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js: $NODE_VER (web dashboard available)"
    HAS_NODE=1
else
    echo -e "${YELLOW}○${NC} Node.js not found (web dashboard won't be available)"
    HAS_NODE=0
fi

# Check Ollama (optional)
if command -v ollama &>/dev/null; then
    echo -e "${GREEN}✓${NC} Ollama detected (local models available)"
elif curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo -e "${GREEN}✓${NC} Ollama running at localhost:11434"
else
    echo -e "${YELLOW}○${NC} Ollama not found. Install at https://ollama.ai for local models"
fi

echo ""

# Clone or update
INSTALL_DIR="$HOME/LifeClaw"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}Updating existing installation...${NC}"
    cd "$INSTALL_DIR"
    git pull --quiet origin main 2>/dev/null || true
else
    echo -e "${CYAN}Cloning LifeClaw...${NC}"
    git clone --quiet https://github.com/slashdoodleart/LifeClaw.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install Python package
echo -e "${CYAN}Installing Python dependencies...${NC}"
pip install -e . --quiet 2>/dev/null || pip3 install -e . --quiet

# Install web dashboard (optional)
if [ "$HAS_NODE" = "1" ]; then
    echo -e "${CYAN}Installing web dashboard...${NC}"
    cd web
    npm install --silent 2>/dev/null || true
    cd ..
fi

# Verify
echo ""
if command -v lifeclaw &>/dev/null; then
    echo -e "${GREEN}${BOLD}✓ LifeClaw installed successfully!${NC}"
else
    echo -e "${GREEN}${BOLD}✓ LifeClaw installed!${NC}"
    echo -e "${YELLOW}  Add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
fi

echo ""
echo -e "  ${BOLD}Next steps:${NC}"
echo -e "  ${CYAN}lifeclaw setup${NC}    — Interactive setup (picks model, theme, MCP)"
echo -e "  ${CYAN}lifeclaw chat${NC}     — Start chatting"
echo -e "  ${CYAN}lifeclaw chat -c${NC}  — Coder mode"
echo ""
