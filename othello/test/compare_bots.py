#!/usr/bin/env python3

import subprocess
import re
from collections import defaultdict
import sys

DESDEMONA = "../Desdemona/bin/Desdemona"
GAMES_PER_MATCHUP = 20

bots = {
    "MyBot": "../Desdemona/bots/MyBot/bot.so",
    "StrongBot": "StrongBot.so",
    "RandomBot": "../Desdemona/bots/RandomBot/RandomBot.so",
    "SlowBot": "../Desdemona/bots/SlowBot/SlowBot.so"
}

stats = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "score": 0})

def run_game(bot1_path, bot2_path):
    """Run a single game and return (black_score, red_score)"""
    try:
        result = subprocess.run(
            [DESDEMONA, bot1_path, bot2_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Parse result
        match = re.search(r'BLACK: (\d+)\s+RED: (\d+)', result.stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT]")
    except Exception as e:
        print(f"  Error running game: {e}")
    return None, None

def main():
    print("=" * 60)
    print(" " * 15 + "OTHELLO BOT COMPARISON")
    print("=" * 60)
    print()
    
    # Run all matchups
    for name1, path1 in bots.items():
        for name2, path2 in bots.items():
            if name1 != name2:
                print(f"\n{name1} vs {name2} ({GAMES_PER_MATCHUP} games)")
                print("-" * 50)
                
                for game in range(GAMES_PER_MATCHUP):
                    black_score, red_score = run_game(path1, path2)
                    
                    if black_score is not None:
                        print(f"  Game {game+1}: {name1}={black_score} {name2}={red_score}", end="")
                        
                        stats[name1]["score"] += black_score
                        stats[name2]["score"] += red_score
                        
                        if black_score > red_score:
                            stats[name1]["wins"] += 1
                            stats[name2]["losses"] += 1
                            print(" [WIN]")
                        elif black_score < red_score:
                            stats[name1]["losses"] += 1
                            stats[name2]["wins"] += 1
                            print(" [LOSS]")
                        else:
                            stats[name1]["draws"] += 1
                            stats[name2]["draws"] += 1
                            print(" [DRAW]")
    
    # Print final statistics
    print("\n" + "=" * 60)
    print(" " * 20 + "FINAL STANDINGS")
    print("=" * 60)
    print(f"{'Bot':<15} {'Wins':>6} {'Loss':>6} {'Draw':>6} {'Score':>8} {'Win%':>8}")
    print("-" * 60)
    
    sorted_bots = sorted(stats.items(), 
                        key=lambda x: (x[1]["wins"], x[1]["score"]), 
                        reverse=True)
    
    for name, s in sorted_bots:
        total = s["wins"] + s["losses"] + s["draws"]
        win_pct = (s["wins"] / total * 100) if total > 0 else 0
        print(f"{name:<15} {s['wins']:>6} {s['losses']:>6} {s['draws']:>6} "
              f"{s['score']:>8} {win_pct:>7.1f}%")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
