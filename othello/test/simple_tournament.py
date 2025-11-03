#!/usr/bin/env python3
"""
Simplified Tournament - Just test MyBot vs StrongBot
"""

import subprocess
import re
import os

GAMES_PER_MATCHUP = 5

def run_game(bot1_path, bot2_path):
    """Run a single game from Desdemona directory"""
    try:
        # Change to Desdemona directory to run
        desdemona_dir = "/home/abhi/College/SMAI/Search-Algorithms-Research/othello/Desdemona"
        
        result = subprocess.run(
            ["./bin/Desdemona", bot1_path, bot2_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=desdemona_dir
        )
        
        # Parse result
        match = re.search(r'BLACK: (\d+)\s+RED: (\d+)', result.stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    except subprocess.TimeoutExpired:
        print("    [TIMEOUT]")
    except Exception as e:
        print(f"    Error: {e}")
    return None, None

def main():
    print("=" * 70)
    print(" " * 20 + "SIMPLE TOURNAMENT")
    print("=" * 70)
    print("\nMyBot vs StrongBot")
    print("-" * 70)
    
    # Paths relative to Desdemona directory
    mybot = "bots/MyBot/bot.so"
    strongbot = "../test/StrongBot.so"
    
    mybot_wins = 0
    strongbot_wins = 0
    draws = 0
    mybot_score = 0
    strongbot_score = 0
    
    # MyBot as BLACK
    print(f"\nRound 1: MyBot (BLACK) vs StrongBot (RED) - {GAMES_PER_MATCHUP} games")
    for i in range(GAMES_PER_MATCHUP):
        black, red = run_game(mybot, strongbot)
        if black is not None:
            print(f"  Game {i+1}: MyBot={black} StrongBot={red}", end="")
            mybot_score += black
            strongbot_score += red
            if black > red:
                mybot_wins += 1
                print(" [WIN]")
            elif black < red:
                strongbot_wins += 1
                print(" [LOSS]")
            else:
                draws += 1
                print(" [DRAW]")
    
    # MyBot as RED
    print(f"\nRound 2: StrongBot (BLACK) vs MyBot (RED) - {GAMES_PER_MATCHUP} games")
    for i in range(GAMES_PER_MATCHUP):
        black, red = run_game(strongbot, mybot)
        if black is not None:
            print(f"  Game {i+1}: StrongBot={black} MyBot={red}", end="")
            mybot_score += red
            strongbot_score += black
            if red > black:
                mybot_wins += 1
                print(" [WIN]")
            elif black > red:
                strongbot_wins += 1
                print(" [LOSS]")
            else:
                draws += 1
                print(" [DRAW]")
    
    # Results
    print("\n" + "=" * 70)
    print(" " * 25 + "FINAL RESULTS")
    print("=" * 70)
    total_games = GAMES_PER_MATCHUP * 2
    mybot_win_pct = (mybot_wins / total_games * 100) if total_games > 0 else 0
    strongbot_win_pct = (strongbot_wins / total_games * 100) if total_games > 0 else 0
    
    print(f"{'Bot':<15} {'Wins':>6} {'Loss':>6} {'Draw':>6} {'Score':>8} {'Win%':>8}")
    print("-" * 70)
    print(f"{'MyBot':<15} {mybot_wins:>6} {strongbot_wins:>6} {draws:>6} {mybot_score:>8} {mybot_win_pct:>7.1f}%")
    print(f"{'StrongBot':<15} {strongbot_wins:>6} {mybot_wins:>6} {draws:>6} {strongbot_score:>8} {strongbot_win_pct:>7.1f}%")
    print("=" * 70)
    
    if mybot_wins > strongbot_wins:
        print("\n🏆 MyBot WINS the tournament!")
    elif strongbot_wins > mybot_wins:
        print("\n🏆 StrongBot WINS the tournament!")
    else:
        print("\n🤝 It's a TIE!")
    print()

if __name__ == "__main__":
    main()
