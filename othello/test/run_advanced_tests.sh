#!/bin/bash
#
# Advanced Othello Bot Testing
# Runs comprehensive tournament and move quality analysis
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "          ADVANCED OTHELLO BOT TESTING SUITE"
echo "================================================================"
echo ""

# Check dependencies
echo "Checking dependencies..."

# Check if MyBot is compiled
if [ ! -f "../Desdemona/bots/MyBot/bot.so" ]; then
    echo "  [!] MyBot not found. Compiling..."
    cd ../Desdemona/bots/MyBot
    make clean && make
    cd "$SCRIPT_DIR"
    if [ -f "../Desdemona/bots/MyBot/bot.so" ]; then
        echo "  [✓] MyBot compiled successfully"
    else
        echo "  [✗] Failed to compile MyBot"
        exit 1
    fi
else
    echo "  [✓] MyBot found"
fi

# Check if StrongBot is compiled
if [ ! -f "StrongBot.so" ]; then
    echo "  [!] StrongBot not found. Compiling..."
    make
    if [ -f "StrongBot.so" ]; then
        echo "  [✓] StrongBot compiled successfully"
    else
        echo "  [✗] Failed to compile StrongBot"
        exit 1
    fi
else
    echo "  [✓] StrongBot found"
fi

# Check if Desdemona executable exists
if [ ! -f "../Desdemona/bin/Desdemona" ]; then
    echo "  [!] Desdemona executable not found. Building..."
    cd ../Desdemona
    make
    cd "$SCRIPT_DIR"
    if [ -f "../Desdemona/bin/Desdemona" ]; then
        echo "  [✓] Desdemona built successfully"
    else
        echo "  [✗] Failed to build Desdemona"
        exit 1
    fi
else
    echo "  [✓] Desdemona found"
fi

# Check for Edax (optional)
if [ -f "../edax-reversi/bin/edax" ]; then
    echo "  [✓] Edax found"
elif [ -d "../edax-reversi/src" ]; then
    echo "  [!] Edax not compiled. Would you like to compile it? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "  [→] Compiling Edax..."
        cd ../edax-reversi/src
        
        # Create bin directory if it doesn't exist
        mkdir -p ../bin
        
        # Try different architectures based on system
        if make build ARCH=x86-64-v3 2>/dev/null; then
            echo "  [✓] Edax compiled with x86-64-v3"
            cd ../bin && ln -sf lEdax-x86-64-v3 edax
        elif make build ARCH=x86-64-v2 2>/dev/null; then
            echo "  [✓] Edax compiled with x86-64-v2"
            cd ../bin && ln -sf lEdax-x86-64-v2 edax
        elif make build ARCH=x86-64 2>/dev/null; then
            echo "  [✓] Edax compiled with x86-64"
            cd ../bin && ln -sf lEdax-x86-64 edax
        else
            echo "  [!] Failed to compile Edax with any architecture. Continuing without it..."
        fi
        
        cd "$SCRIPT_DIR"
        if [ -f "../edax-reversi/bin/edax" ]; then
            echo "  [✓] Edax available for testing"
        fi
    else
        echo "  [!] Skipping Edax. Move quality analysis will be limited."
    fi
else
    echo "  [!] Edax not found. Move quality analysis will be limited."
fi

# Check for Egaroucid (optional)
if [ -f "../Egaroucid/bin/Egaroucid_for_Console.out" ]; then
    echo "  [✓] Egaroucid found"
else
    echo "  [!] Egaroucid not found. Move quality analysis will be limited."
fi

echo ""
echo "================================================================"
echo "                    STARTING TESTS"
echo "================================================================"
echo ""

# Make script executable
chmod +x advanced_tournament.py

# Run the advanced tournament
python3 advanced_tournament.py

echo ""
echo "================================================================"
echo "                    TESTS COMPLETE"
echo "================================================================"
echo ""
echo "Summary:"
echo "  1. Tournament results show head-to-head win rates"
echo "  2. Move quality rankings show positional understanding"
echo ""
echo "For quick tests, use: ./quick_test.sh"
echo "For basic tournament: ./tournament.sh"
echo ""
