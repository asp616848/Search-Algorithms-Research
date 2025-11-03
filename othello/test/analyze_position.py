#!/usr/bin/env python3
"""
Position Analyzer - Test bot decisions at specific positions
Usage: python3 analyze_position.py [move1 move2 move3 ...]
Example: python3 analyze_position.py c4 c5 d5 c3
"""

import sys
import subprocess
import re
import os

EDAX_PATH = "../edax-reversi/bin/edax"
EGAROUCID_PATH = "../Egaroucid/bin/Egaroucid_for_Console.out"

def analyze_position(moves):
    """Analyze a position and get recommendations from available engines"""
    
    print("=" * 70)
    print(f"Position Analysis: {' '.join(moves)}")
    print("=" * 70)
    print(f"\nAfter {len(moves)} moves: {' -> '.join(moves)}")
    print("\nBot Recommendations:")
    print("-" * 70)
    
    recommendations = {}
    
    # Try Edax
    if os.path.exists(EDAX_PATH):
        try:
            edax_moves = " ".join([m.upper() for m in moves])
            cmd = f'echo "mode 2\nlevel 10\nsetboard {edax_moves}\ngo\n" | {EDAX_PATH} -q'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(EDAX_PATH)
            )
            
            # Parse output
            for line in result.stdout.split('\n'):
                if '-->' in line or 'best' in line.lower():
                    match = re.search(r'([A-H][1-8])', line, re.IGNORECASE)
                    if match:
                        move = match.group(1).lower()
                        # Try to extract score if available
                        score_match = re.search(r'([-+]?\d+)', line)
                        score = score_match.group(1) if score_match else "N/A"
                        recommendations["Edax"] = (move, score)
                        print(f"  Edax         : {move} (eval: {score})")
                        break
            
            if "Edax" not in recommendations:
                print(f"  Edax         : [could not parse output]")
        except Exception as e:
            print(f"  Edax         : [error: {e}]")
    else:
        print(f"  Edax         : [not available - compile with: cd ../edax-reversi/src && make build ARCH=x64-modern]")
    
    # Try Egaroucid
    if os.path.exists(EGAROUCID_PATH):
        try:
            moves_str = " ".join(moves)
            result = subprocess.run(
                [EGAROUCID_PATH],
                input=f"setboard {moves_str}\ngo\n",
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                match = re.search(r'([a-h][0-7])', line)
                if match:
                    move = match.group(1)
                    recommendations["Egaroucid"] = (move, "N/A")
                    print(f"  Egaroucid    : {move}")
                    break
            
            if "Egaroucid" not in recommendations:
                print(f"  Egaroucid    : [could not parse output]")
        except Exception as e:
            print(f"  Egaroucid    : [error: {e}]")
    else:
        print(f"  Egaroucid    : [not available]")
    
    # Note about Desdemona bots
    print(f"  MyBot        : [requires game state - use advanced_tournament.py]")
    print(f"  StrongBot    : [requires game state - use advanced_tournament.py]")
    
    print("-" * 70)
    
    # Analysis
    if len(recommendations) == 0:
        print("\n⚠️  No engines available for analysis")
        print("   Compile Edax for position analysis:")
        print("   cd ../edax-reversi/src && make build ARCH=x64-modern")
    elif len(recommendations) == 1:
        print(f"\n✓ Recommendation: {list(recommendations.values())[0][0]}")
    else:
        moves_suggested = [rec[0] for rec in recommendations.values()]
        if len(set(moves_suggested)) == 1:
            print(f"\n✓ Strong Consensus: {moves_suggested[0]} (all engines agree)")
        else:
            print(f"\n⚠️  Engines disagree:")
            for engine, (move, score) in recommendations.items():
                print(f"     {engine}: {move}")
    
    print("=" * 70)
    return recommendations


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_position.py [move1 move2 move3 ...]")
        print("\nExample positions:")
        print("  Opening:     python3 analyze_position.py c4 c5 d5")
        print("  Mid-game:    python3 analyze_position.py c4 c5 d5 c3 c2 e5 d6")
        print("  From log:    python3 analyze_position.py $(head -n 10 ../Desdemona/game.log | tr '\\n' ' ')")
        print("\nAvailable test positions:")
        print("  1. python3 analyze_position.py c4 c5 d5")
        print("  2. python3 analyze_position.py c4 c5 d5 c3 c2 e5 d6")
        print("  3. python3 analyze_position.py c4 c5 d5 c3 b3 c2 b5")
        sys.exit(1)
    
    moves = sys.argv[1:]
    
    # Validate moves (basic check)
    for move in moves:
        if len(move) != 2 or move[0] not in 'abcdefgh' or move[1] not in '01234567':
            print(f"⚠️  Invalid move format: {move}")
            print("   Moves should be like: c4, d5, e6, etc.")
            sys.exit(1)
    
    analyze_position(moves)


if __name__ == "__main__":
    main()
