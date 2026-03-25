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

# Find the best available Python 3.11+
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" &>/dev/null; then
        PY_VER=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

# Also check Homebrew paths explicitly (macOS)
if [ -z "$PYTHON" ]; then
    for brew_py in /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11; do
        if [ -x "$brew_py" ]; then
            PY_VER=$("$brew_py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
            PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
            PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
            if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
                PYTHON="$brew_py"
                break
            fi
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗${NC} Python 3.11+ required."
    echo -e "  Your system has: $(python3 --version 2>&1 || echo 'none')"
    echo -e "  Install via: ${CYAN}brew install python@3.11${NC} or ${CYAN}https://python.org${NC}"
    exit 1
fi

PY_FULL=$("$PYTHON" --version 2>&1)
echo -e "${GREEN}✓${NC} Python: $PY_FULL ($PYTHON)"

# Get matching pip
PIP="$PYTHON -m pip"

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

# Install Python package using the correct Python
echo -e "${CYAN}Installing Python dependencies...${NC}"
$PIP install -e . --quiet 2>/dev/null || $PIP install -e .

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
    # Check if it's in the Python scripts dir
    SCRIPTS_DIR=$($PYTHON -c "import sysconfig; print(sysconfig.get_path('scripts'))" 2>/dev/null || echo "")
    if [ -n "$SCRIPTS_DIR" ] && [ -f "$SCRIPTS_DIR/lifeclaw" ]; then
        echo -e "${GREEN}${BOLD}✓ LifeClaw installed!${NC}"
        echo -e "${YELLOW}  Add to PATH: export PATH=\"$SCRIPTS_DIR:\$PATH\"${NC}"
    else
        echo -e "${GREEN}${BOLD}✓ LifeClaw installed!${NC}"
        echo -e "${YELLOW}  If 'lifeclaw' isn't found, add to PATH:${NC}"
        echo -e "${YELLOW}    export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        echo -e "${YELLOW}  Or run directly: $PYTHON -m lifeclaw${NC}"
    fi
fi

echo ""
echo -e "  ${BOLD}Next steps:${NC}"
echo -e "  ${CYAN}lifeclaw setup${NC}    — Interactive setup (picks model, theme, MCP)"
echo -e "  ${CYAN}lifeclaw chat${NC}     — Start chatting"
echo -e "  ${CYAN}lifeclaw chat -c${NC}  — Coder mode"
echo ""
