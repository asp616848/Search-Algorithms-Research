# Advanced Othello Bot Testing System

## Overview

This testing system provides **two distinct ranking methods** for Othello bots:

1. **Tournament Ranking** - Win/loss record from actual games
2. **Move Quality Ranking** - Positional understanding measured by agreement with strong engines

## Files Created

### Main Scripts

1. **`advanced_tournament.py`** - Comprehensive testing framework
   - Runs round-robin tournament between Desdemona bots
   - Analyzes move quality at critical positions using Edax/Egaroucid
   - Produces two separate rankings

2. **`run_advanced_tests.sh`** - Automated test runner
   - Checks and compiles all dependencies
   - Offers to compile Edax if available
   - Runs the full test suite

3. **`analyze_position.py`** - Standalone position analyzer
   - Tests any specific board position
   - Gets recommendations from all available engines
   - Useful for debugging specific moves

### Updated Files

4. **`README.md`** - Complete documentation
   - Usage instructions
   - Explanation of both ranking systems
   - Tips for improvement based on results

## How to Use

### Option 1: Full Automated Test (Recommended)

```bash
cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/test
./run_advanced_tests.sh
```

This will:
- Compile all necessary components
- Run tournament between MyBot and StrongBot
- Analyze move quality at 5 critical positions
- Show both rankings

### Option 2: Manual Python Script

```bash
cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/test
python3 advanced_tournament.py
```

### Option 3: Analyze Specific Position

```bash
cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/test
python3 analyze_position.py c4 c5 d5 c3
```

## Understanding the Two Rankings

### Tournament Ranking
**What it measures:** Overall game-playing strength
- Win/loss record from actual games
- Total pieces captured
- Performance against different opponents

**Example:**
```
Rank   Bot           W     L     D    Score     Win%
1      StrongBot    16    4     0     1024     80.0%
2      MyBot        12    8     0      956     60.0%
```

### Move Quality Ranking
**What it measures:** Positional understanding and tactical accuracy
- Compares bot decisions at critical positions
- Measures agreement with world-class engines (Edax/Egaroucid)
- Tests 5 carefully selected positions covering different game phases

**Example:**
```
Rank   Bot          Tested   Agrees   Differs   Consensus%
1      StrongBot        5        4        1        80.0%
2      MyBot            5        3        2        60.0%
```

## Test Positions

The move quality analysis tests these 5 positions:

1. **Opening Position** - After 3 moves (c4 c5 d5)
2. **Mid-Game Complex** - After 12 moves with tactical choices
3. **Corner Decision** - Testing corner capture understanding
4. **Edge Control** - Testing edge strategy
5. **Late Endgame** - Testing endgame technique

## Interpreting Results

### Case 1: Good Tournament, Good Move Quality ✅
- Your bot is strong overall
- Good understanding of positions
- Ready for competition

### Case 2: Good Tournament, Poor Move Quality ⚠️
- Bot wins games but makes suboptimal moves
- Might be exploiting weaknesses in specific opponents
- Need to improve evaluation function
- Study positions where you disagree with engines

### Case 3: Poor Tournament, Good Move Quality 🤔
- Bot understands positions but fails in execution
- Possible issues:
  - Time management problems
  - Search depth too shallow
  - Bugs in minimax/alpha-beta
  - Evaluation weights need tuning

### Case 4: Poor Tournament, Poor Move Quality ⚠️
- Start with improving evaluation function
- Study the test positions
- Compare your positional weights with StrongBot

## Requirements

### Mandatory
- Desdemona framework (already present)
- MyBot compiled (`cd ../Desdemona/bots/MyBot && make`)
- StrongBot compiled (`cd . && make`)

### Optional (for move quality analysis)
- **Edax**: Compile with:
  ```bash
  cd ../edax-reversi/src
  # Try in order until one works:
  make build ARCH=x86-64-v3  # Modern CPUs (2015+)
  # OR
  make build ARCH=x86-64-v2  # Older CPUs
  # OR  
  make build ARCH=x86-64     # Any x86-64 CPU
  ```
- **Egaroucid**: Already available if `../Egaroucid/bin/Egaroucid_for_Console.out` exists

## Architecture

```
advanced_tournament.py
├── TournamentManager
│   ├── run_tournament()           # Round-robin games
│   └── run_move_quality_analysis() # Position testing
│
├── BotInterface (Abstract)
│   ├── DesdemonaBot              # MyBot, StrongBot
│   ├── EdaxBot                   # Edax engine
│   └── EgaroucidBot              # Egaroucid engine
│
└── Results
    ├── Tournament Rankings
    └── Move Quality Rankings
```

## Example Output

```
======================================================================
                  ADVANCED OTHELLO BOT TESTING
======================================================================

Initializing bots...
  ✓ MyBot added to tournament
  ✓ StrongBot added to tournament
  ✓ Edax added to tournament
  ✗ Egaroucid not available

======================================================================
                    ROUND-ROBIN TOURNAMENT
======================================================================

MyBot vs StrongBot
--------------------------------------------------
  Game 1: MyBot=32 vs StrongBot=32 [DRAW]
  Game 2: MyBot=28 vs StrongBot=36 [LOSS]
  ...

======================================================================
                    TOURNAMENT RANKINGS
======================================================================
Rank   Bot              W     L     D    Score     Win%
----------------------------------------------------------------------
1      StrongBot       14    4     2     1056     70.0%
2      MyBot           10    8     2      944     50.0%
======================================================================

======================================================================
                   MOVE QUALITY ANALYSIS
======================================================================

Analyzing bot decisions at critical positions...

1. Opening Position 1
   Early opening after 3 moves
   Position after moves: c4 c5 d5
----------------------------------------------------------------------
   Edax           would play: c3
   StrongBot      [N/A - requires game state]
   MyBot          [N/A - requires game state]

   Consensus: c3 (1/1 bots agree)

...

======================================================================
                   MOVE QUALITY RANKINGS
======================================================================
Rank   Bot             Tested   Agrees   Differs   Consensus%
----------------------------------------------------------------------
1      Edax                5        5        0       100.0%

Note: Higher consensus % indicates stronger positional play
      (More agreement with other strong engines)
```

## Extending the System

### Adding New Test Positions

Edit `advanced_tournament.py` and add to `TEST_POSITIONS`:

```python
{
    "name": "Your Position Name",
    "moves": ["c4", "c5", "d5", ...],
    "description": "What this position tests"
}
```

### Adding New Bots

Add bot to tournament in `main()`:

```python
newbot = DesdemonaBot("NewBot", "path/to/bot.so")
manager.add_bot(newbot)
```

### Adjusting Tournament Length

Change `GAMES_PER_MATCHUP` at the top of `advanced_tournament.py`:

```python
GAMES_PER_MATCHUP = 20  # More games = more accurate
```

## Troubleshooting

### "Edax not found"
```bash
cd ../edax-reversi/src
# Try these in order until one works:
make build ARCH=x86-64-v3  # For modern CPUs (recommended)
# If that fails:
make build ARCH=x86-64-v2  # For older CPUs
# If that fails:
make build ARCH=x86-64     # Basic build (slowest but works on all x86-64)
```

### "MyBot compilation failed"
```bash
cd ../Desdemona/bots/MyBot
make clean && make
```

### "StrongBot compilation failed"
```bash
cd /home/abhi/College/SMAI/Search-Algorithms-Research/othello/test
make clean && make
```

### "Games timing out"
- Check MyBot.cpp for infinite loops
- Verify time management (should stay under 2 seconds)
- Look for stderr output: `tail -f ../Desdemona/game.log`

## Performance Tips

1. **If losing to StrongBot badly:**
   - Study StrongBot.cpp evaluation function
   - Compare your weights with StrongBot's
   - Check your search depth

2. **If move quality is low:**
   - Use `analyze_position.py` to study specific positions
   - Compare your move with Edax's recommendation
   - Adjust evaluation weights

3. **If games are slow:**
   - Improve alpha-beta pruning
   - Better move ordering
   - Add transposition tables (see StrongBot)

## Next Steps

1. Run `./run_advanced_tests.sh` to get baseline
2. Study positions where you disagree with Edax
3. Improve evaluation function
4. Re-run tests to measure improvement
5. Iterate!

---

Created: 2025-11-03
For: SMAI Assignment - Othello Bot Development
