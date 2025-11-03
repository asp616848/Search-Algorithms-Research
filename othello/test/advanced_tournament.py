#!/usr/bin/env python3
"""
Advanced Othello Bot Tournament System
Tests MyBot, StrongBot, Edax, and Egaroucid
Includes:
1. Round-robin tournament with full ranking
2. Move quality analysis at specific positions
"""

import subprocess
import re
import os
import sys
import json
from collections import defaultdict
from pathlib import Path

# Configuration
DESDEMONA = "../Desdemona/bin/Desdemona"
EDAX_PATH = "../edax-reversi/bin/edax"
EGAROUCID_PATH = "../Egaroucid/bin/Egaroucid_for_Console.out"
GAMES_PER_MATCHUP = 5  # Reduced from 10 for faster testing

# Test positions for move quality analysis (various game stages)
TEST_POSITIONS = [
    {
        "name": "Opening Position 1",
        "moves": ["c4", "c5", "d5"],
        "description": "Early opening after 3 moves"
    },
    {
        "name": "Mid-Game Position 1", 
        "moves": ["c4", "c5", "d5", "c3", "c2", "e5", "d6", "e2", "d2", "c1", "b5", "d7"],
        "description": "Complex mid-game position"
    },
    {
        "name": "Corner Decision",
        "moves": ["c4", "c5", "d5", "c3", "c2", "e5", "d6"],
        "description": "Decision involving corner control"
    },
    {
        "name": "Edge Control",
        "moves": ["c4", "c5", "d5", "c3", "b3", "c2", "b5"],
        "description": "Edge control scenario"
    },
    {
        "name": "End Game Position",
        "moves": ["c4", "c5", "d5", "c3", "c2", "e5", "d6", "e2", "d2", "c1", 
                  "b5", "d7", "c0", "a5", "f2", "b3", "f4", "d1", "e6", "f7",
                  "c6", "b2", "c7", "b4", "d0", "f3", "g2", "h2"],
        "description": "Late endgame with limited moves"
    }
]


class BotInterface:
    """Base class for bot interfaces"""
    
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.available = self.check_availability()
    
    def check_availability(self):
        """Check if bot is available"""
        return os.path.exists(self.path)
    
    def get_move(self, position_moves):
        """Get bot's move for a given position. To be overridden."""
        raise NotImplementedError
    
    def play_game_as_black(self, opponent):
        """Play a game as black against opponent"""
        raise NotImplementedError


class DesdemonaBot(BotInterface):
    """Interface for Desdemona bots"""
    
    def play_game(self, opponent, as_black=True):
        """Play a game via Desdemona"""
        try:
            # Set up environment for Desdemona
            env = os.environ.copy()
            desdemona_base = os.path.abspath("../Desdemona")
            env["LD_LIBRARY_PATH"] = f"{desdemona_base}/lib:" + env.get("LD_LIBRARY_PATH", "")
            
            # Convert bot paths to absolute paths
            bot1_path = os.path.abspath(self.path)
            bot2_path = os.path.abspath(opponent.path)
            
            if as_black:
                result = subprocess.run(
                    [DESDEMONA, bot1_path, bot2_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env
                )
            else:
                result = subprocess.run(
                    [DESDEMONA, bot2_path, bot1_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env
                )
            
            match = re.search(r'BLACK: (\d+)\s+RED: (\d+)', result.stdout)
            if match:
                black_score = int(match.group(1))
                red_score = int(match.group(2))
                return (black_score, red_score) if as_black else (red_score, black_score)
        except Exception as e:
            print(f"    Error in game: {e}")
        return None, None


class EdaxBot(BotInterface):
    """Interface for Edax engine"""
    
    def __init__(self):
        super().__init__("Edax", EDAX_PATH)
    
    def check_availability(self):
        """Check if Edax is compiled"""
        if not os.path.exists(self.path):
            print(f"  [INFO] Edax not found at {self.path}")
            print(f"  [INFO] To compile: cd ../edax-reversi/src && make build ARCH=x64-modern")
            return False
        return True
    
    def get_move(self, position_moves, level=10):
        """Get Edax's best move for a position"""
        if not self.available:
            return None
        
        try:
            # Convert moves to Edax format
            edax_moves = " ".join([self._to_edax_format(m) for m in position_moves])
            
            # Create Edax command
            cmd = f'echo "mode 2\nlevel {level}\nsetboard {edax_moves}\ngo\n" | {self.path} -q'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(self.path)
            )
            
            # Parse Edax output for best move
            for line in result.stdout.split('\n'):
                if 'best move' in line.lower() or '-->' in line:
                    match = re.search(r'([A-H][1-8])', line, re.IGNORECASE)
                    if match:
                        return match.group(1).lower()
            
            return None
        except Exception as e:
            print(f"    Error getting Edax move: {e}")
            return None
    
    def _to_edax_format(self, move):
        """Convert desdemona format (c4) to Edax format (C4)"""
        return move.upper()


class EgaroucidBot(BotInterface):
    """Interface for Egaroucid engine"""
    
    def __init__(self):
        super().__init__("Egaroucid", EGAROUCID_PATH)
    
    def check_availability(self):
        """Check if Egaroucid is available"""
        if not os.path.exists(self.path):
            print(f"  [INFO] Egaroucid not found at {self.path}")
            return False
        return True
    
    def get_move(self, position_moves, level=10):
        """Get Egaroucid's best move for a position"""
        if not self.available:
            return None
        
        try:
            # Egaroucid console interface might differ
            # This is a placeholder - actual implementation depends on Egaroucid's CLI
            moves_str = " ".join(position_moves)
            
            # Try to invoke Egaroucid (exact format may need adjustment)
            result = subprocess.run(
                [self.path],
                input=f"setboard {moves_str}\ngo\n",
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse output (format may vary)
            for line in result.stdout.split('\n'):
                match = re.search(r'([a-h][0-7])', line)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            print(f"    Error getting Egaroucid move: {e}")
            return None


class TournamentManager:
    """Manages tournament between bots"""
    
    def __init__(self):
        self.bots = []
        self.stats = defaultdict(lambda: {
            "wins": 0, "losses": 0, "draws": 0, 
            "score": 0, "games_played": 0
        })
        self.move_quality_scores = defaultdict(lambda: {
            "agreements": 0, "disagreements": 0, "positions_tested": 0
        })
    
    def add_bot(self, bot):
        """Add a bot to the tournament"""
        if bot.available:
            self.bots.append(bot)
            print(f"  ✓ {bot.name} added to tournament")
        else:
            print(f"  ✗ {bot.name} not available")
    
    def run_tournament(self):
        """Run round-robin tournament"""
        print("\n" + "=" * 70)
        print(" " * 20 + "ROUND-ROBIN TOURNAMENT")
        print("=" * 70)
        
        if len(self.bots) < 2:
            print("  [ERROR] Need at least 2 bots for tournament")
            return
        
        # Only run tournaments between Desdemona bots
        desdemona_bots = [b for b in self.bots if isinstance(b, DesdemonaBot)]
        
        if len(desdemona_bots) < 2:
            print("  [INFO] Need at least 2 Desdemona bots for full tournament")
            return
        
        for i, bot1 in enumerate(desdemona_bots):
            for bot2 in desdemona_bots[i+1:]:
                self._play_matchup(bot1, bot2)
        
        self._print_tournament_results()
    
    def _play_matchup(self, bot1, bot2):
        """Play a matchup between two bots"""
        print(f"\n{bot1.name} vs {bot2.name}")
        print("-" * 50)
        
        for game_num in range(GAMES_PER_MATCHUP):
            # Bot1 as black
            score1, score2 = bot1.play_game(bot2, as_black=True)
            if score1 is not None:
                self._record_game(bot1.name, bot2.name, score1, score2, game_num * 2 + 1)
            
            # Bot2 as black (swap colors)
            score2, score1 = bot2.play_game(bot1, as_black=True)
            if score1 is not None:
                self._record_game(bot1.name, bot2.name, score1, score2, game_num * 2 + 2)
    
    def _record_game(self, name1, name2, score1, score2, game_num):
        """Record game results"""
        print(f"  Game {game_num}: {name1}={score1} vs {name2}={score2}", end="")
        
        self.stats[name1]["score"] += score1
        self.stats[name2]["score"] += score2
        self.stats[name1]["games_played"] += 1
        self.stats[name2]["games_played"] += 1
        
        if score1 > score2:
            self.stats[name1]["wins"] += 1
            self.stats[name2]["losses"] += 1
            print(" [WIN]")
        elif score1 < score2:
            self.stats[name1]["losses"] += 1
            self.stats[name2]["wins"] += 1
            print(" [LOSS]")
        else:
            self.stats[name1]["draws"] += 1
            self.stats[name2]["draws"] += 1
            print(" [DRAW]")
    
    def _print_tournament_results(self):
        """Print final tournament standings"""
        print("\n" + "=" * 70)
        print(" " * 22 + "TOURNAMENT RANKINGS")
        print("=" * 70)
        print(f"{'Rank':<6} {'Bot':<15} {'W':>5} {'L':>5} {'D':>5} {'Score':>8} {'Win%':>8}")
        print("-" * 70)
        
        sorted_bots = sorted(
            self.stats.items(),
            key=lambda x: (x[1]["wins"], x[1]["score"], -x[1]["losses"]),
            reverse=True
        )
        
        for rank, (name, s) in enumerate(sorted_bots, 1):
            total = s["games_played"]
            win_pct = (s["wins"] / total * 100) if total > 0 else 0
            print(f"{rank:<6} {name:<15} {s['wins']:>5} {s['losses']:>5} {s['draws']:>5} "
                  f"{s['score']:>8} {win_pct:>7.1f}%")
        
        print("=" * 70)
    
    def run_move_quality_analysis(self):
        """Analyze move quality at specific positions"""
        print("\n" + "=" * 70)
        print(" " * 18 + "MOVE QUALITY ANALYSIS")
        print("=" * 70)
        print("\nAnalyzing bot decisions at critical positions...")
        print("(Comparing moves chosen by different bots)\n")
        
        results = []
        
        for pos_idx, position in enumerate(TEST_POSITIONS, 1):
            print(f"\n{pos_idx}. {position['name']}")
            print(f"   {position['description']}")
            print(f"   Position after moves: {' '.join(position['moves'])}")
            print("-" * 70)
            
            moves = {}
            for bot in self.bots:
                move = self._get_bot_move_for_position(bot, position['moves'])
                moves[bot.name] = move
                if move:
                    print(f"   {bot.name:<15} would play: {move}")
                else:
                    print(f"   {bot.name:<15} [error getting move]")
            
            # Analyze consensus
            move_counts = defaultdict(int)
            for bot_name, move in moves.items():
                if move:
                    move_counts[move] += 1
            
            if move_counts:
                consensus_move = max(move_counts.items(), key=lambda x: x[1])
                print(f"\n   Consensus: {consensus_move[0]} ({consensus_move[1]}/{len([m for m in moves.values() if m])} bots agree)")
                
                # Score bots based on agreement with consensus
                for bot_name, move in moves.items():
                    if move:
                        self.move_quality_scores[bot_name]["positions_tested"] += 1
                        if move == consensus_move[0]:
                            self.move_quality_scores[bot_name]["agreements"] += 1
                        else:
                            self.move_quality_scores[bot_name]["disagreements"] += 1
            
            results.append({
                "position": position['name'],
                "moves": moves
            })
        
        self._print_move_quality_rankings()
        return results
    
    def _get_bot_move_for_position(self, bot, moves):
        """Get bot's move recommendation for a position"""
        if isinstance(bot, EdaxBot):
            return bot.get_move(moves)
        elif isinstance(bot, EgaroucidBot):
            return bot.get_move(moves)
        elif isinstance(bot, DesdemonaBot):
            # For Desdemona bots, we'd need to create a game state
            # This is more complex and would require modifying the bot interface
            # For now, return None
            return "[N/A - requires game state]"
        return None
    
    def _print_move_quality_rankings(self):
        """Print move quality rankings"""
        print("\n" + "=" * 70)
        print(" " * 18 + "MOVE QUALITY RANKINGS")
        print("=" * 70)
        print(f"{'Rank':<6} {'Bot':<15} {'Tested':>8} {'Agrees':>8} {'Differs':>8} {'Consensus%':>12}")
        print("-" * 70)
        
        # Filter and sort bots that were actually tested
        tested_bots = [(name, scores) for name, scores in self.move_quality_scores.items() 
                      if scores["positions_tested"] > 0]
        
        sorted_bots = sorted(
            tested_bots,
            key=lambda x: x[1]["agreements"] / x[1]["positions_tested"] if x[1]["positions_tested"] > 0 else 0,
            reverse=True
        )
        
        for rank, (name, scores) in enumerate(sorted_bots, 1):
            tested = scores["positions_tested"]
            agrees = scores["agreements"]
            differs = scores["disagreements"]
            consensus_pct = (agrees / tested * 100) if tested > 0 else 0
            
            print(f"{rank:<6} {name:<15} {tested:>8} {agrees:>8} {differs:>8} {consensus_pct:>11.1f}%")
        
        print("=" * 70)
        print("\nNote: Higher consensus % indicates stronger positional play")
        print("      (More agreement with other strong engines)")


def main():
    """Main function"""
    print("=" * 70)
    print(" " * 15 + "ADVANCED OTHELLO BOT TESTING")
    print("=" * 70)
    print("\nInitializing bots...")
    
    manager = TournamentManager()
    
    # Add Desdemona bots
    mybot = DesdemonaBot("MyBot", "../Desdemona/bots/MyBot/bot.so")
    strongbot = DesdemonaBot("StrongBot", "StrongBot.so")
    
    manager.add_bot(mybot)
    manager.add_bot(strongbot)
    
    # Add external engines
    edax = EdaxBot()
    egaroucid = EgaroucidBot()
    
    manager.add_bot(edax)
    manager.add_bot(egaroucid)
    
    # Check if we can run tournament
    if len([b for b in manager.bots if isinstance(b, DesdemonaBot)]) >= 2:
        # Run tournament
        manager.run_tournament()
    else:
        print("\n[INFO] Not enough Desdemona bots for tournament")
    
    # Run move quality analysis (requires engines)
    if any(isinstance(b, (EdaxBot, EgaroucidBot)) and b.available for b in manager.bots):
        manager.run_move_quality_analysis()
    else:
        print("\n[INFO] External engines (Edax/Egaroucid) needed for move quality analysis")
        print("[INFO] Run: cd ../edax-reversi/src && make build ARCH=x64-modern")
    
    print("\n" + "=" * 70)
    print(" " * 23 + "TESTING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
