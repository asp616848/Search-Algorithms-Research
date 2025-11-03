# Othello Bot Testing Suite

This folder contains testing scripts and a strong reference bot for comparing your Othello bot implementations.

## Files

- **StrongBot.cpp** - Advanced Othello bot with negamax, transposition tables, and sophisticated evaluation
- **advanced_tournament.py** - Comprehensive testing with tournament + move quality analysis ⭐ **NEW**
- **run_advanced_tests.sh** - Automated runner for advanced tournament ⭐ **NEW**
- **tournament.sh** - Run a full round-robin tournament between all bots
- **quick_test.sh** - Quick head-to-head test (5 games each color)
- **compare_bots.py** - Python script for comprehensive statistical comparison

## Quick Start

### Best Option: Advanced Tournament (Recommended)

Tests your bot with **TWO different ranking systems**:

```bash
chmod +x run_advanced_tests.sh
./run_advanced_tests.sh
```

This will:
1. **Tournament Ranking**: Full round-robin with win/loss records
2. **Move Quality Ranking**: Analyzes decisions at critical positions against Edax/Egaroucid

### Alternative: Manual Testing

### 1. Compile StrongBot

```bash
cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/test
make
```

### 2. Quick Test (Recommended First)

Test MyBot vs StrongBot with 10 games total:

```bash
chmod +x quick_test.sh
./quick_test.sh
```

### 3. Full Tournament

Run a complete round-robin tournament:

```bash
chmod +x tournament.sh
./tournament.sh
```

This runs 10 games for each bot pair (both colors) and provides final standings.

### 4. Statistical Analysis (Python)

For detailed statistics with 20 games per matchup:

```bash
chmod +x compare_bots.py
python3 compare_bots.py
```

### 5. Individual Matchups

Test specific matchups manually:

```bash
# MyBot vs StrongBot
../Desdemona/bin/Desdemona ../Desdemona/bots/MyBot/bot.so StrongBot.so

# Multiple games
for i in {1..10}; do
    ../Desdemona/bin/Desdemona ../Desdemona/bots/MyBot/bot.so StrongBot.so | grep Result
done
```

## Bots Available

- **MyBot** - Your main bot (Minimax with alpha-beta pruning)
- **StrongBot** - Advanced reference bot (Negamax with transposition tables)
- **RandomBot** - Makes random valid moves
- **SlowBot** - Simple bot for testing

## StrongBot Features

StrongBot is designed to be a strong opponent with:

- Negamax algorithm (cleaner minimax variant)
- Transposition table (position caching)
- Advanced move ordering with X-square detection
- 6-component evaluation function:
  - Coin parity (piece count)
  - Mobility (move options)
  - Corner control
  - Stability
  - Potential mobility
  - Positional weights
- Game-phase aware strategy (opening/midgame/endgame)
- Iterative deepening up to depth 12

## Interpreting Results

- **Win Rate**: Percentage of games won
- **Total Score**: Sum of all pieces captured across all games
- **Against RandomBot**: Should win 100% (easy baseline)
- **Against SlowBot**: Should win 95%+ (moderate baseline)
- **Against StrongBot**: Competitive performance (50%+ is good)

## Tips

1. Start with `quick_test.sh` for rapid feedback
2. Use `tournament.sh` for comprehensive comparison
3. Check that MyBot wins consistently against RandomBot and SlowBot
4. Competitive performance against StrongBot indicates tournament readiness
5. Monitor execution times (should stay under 2 seconds per move)

## Note on Edax

Edax is a world-championship level engine but requires special integration to work with Desdemona. StrongBot provides a strong reference within the Desdemona framework.

## Advanced Tournament Details

### Tournament Ranking
- **Win Rate**: Head-to-head game results
- **Total Score**: Cumulative pieces across all games
- **Methodology**: Round-robin with color swapping (each pair plays both colors)

### Move Quality Ranking
- **Consensus Analysis**: Compares bot moves at critical positions
- **Scoring**: Bots that agree with stronger engines (Edax/Egaroucid) get higher scores
- **Test Positions**: 5 carefully selected positions:
  - Early opening
  - Mid-game complexity
  - Corner decisions
  - Edge control
  - Late endgame

**Why Two Rankings?**
- **Tournament Ranking** = Overall strength in actual games
- **Move Quality Ranking** = Positional understanding and tactical accuracy

A bot might win games (good tournament ranking) but make suboptimal moves that happen to work against specific opponents. Move quality ranking reveals true understanding.

## Example Output

```
==================== TOURNAMENT RANKINGS ====================
Rank   Bot              W     L     D    Score     Win%
----------------------------------------------------------------
1      StrongBot        16    4     0     1024     80.0%
2      MyBot            12    8     0      956     60.0%

================== MOVE QUALITY RANKINGS ====================
Rank   Bot             Tested   Agrees   Differs   Consensus%
----------------------------------------------------------------
1      StrongBot           5        4        1        80.0%
2      MyBot               5        3        2        60.0%
```

## Requirements

**Mandatory:**
- Desdemona framework (parent directory)
- MyBot compiled
- StrongBot compiled

**Optional (for move quality analysis):**
- Edax engine (compile with: `cd ../edax-reversi/src && make build ARCH=x86-64-v3`)
- Egaroucid engine

## Tips for Improvement

1. **If Tournament Rank is Good but Move Quality is Low:**
   - Your bot is tactically weak but strategically lucky
   - Improve evaluation function
   - Study positions where you disagree with engines

2. **If Move Quality is Good but Tournament Rank is Low:**
   - Your bot understands positions but fails in execution
   - Check for time management issues
   - Increase search depth
   - Fix bugs in game tree search

3. **Both Rankings Low:**
   - Start with improving evaluation function
   - Study the test positions
   - Compare your moves with engine analysis


