# Othello Bot Testing Suite

This folder contains testing scripts and a strong reference bot for comparing your Othello bot implementations.

## Files

- **StrongBot.cpp** - Advanced Othello bot with negamax, transposition tables, and sophisticated evaluation
- **tournament.sh** - Run a full round-robin tournament between all bots
- **quick_test.sh** - Quick head-to-head test (5 games each color)
- **compare_bots.py** - Python script for comprehensive statistical comparison

## Usage

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
