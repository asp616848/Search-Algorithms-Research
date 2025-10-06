# Keyboard Interrupt Fix for Multiprocessing on Windows

## Problem
When running the TSP solver on Windows, pressing Ctrl+C (KeyboardInterrupt) didn't properly stop the program. The worker processes would hang and the program wouldn't terminate gracefully.

## Root Cause
On Windows, Python's `multiprocessing` module uses the "spawn" start method by default (unlike "fork" on Linux/Mac). With spawn, child processes don't inherit the parent's signal handlers, and SIGINT (Ctrl+C) signals don't propagate cleanly to worker processes in a Pool.

## Solution Implemented

### 1. Worker Process Signal Handling (`heuristics.py`)
```python
def _ls_worker_init(dist_matrix, neighbor_lists):
    # Workers ignore SIGINT - let parent handle it
    signal.signal(signal.SIGINT, signal.SIG_IGN)
```

This tells worker processes to ignore Ctrl+C signals entirely. Only the main process will handle the interrupt.

### 2. Improved Pool Cleanup (`heuristics.py`)
```python
except (KeyboardInterrupt, Exception) as e:
    # Terminate pool immediately on interrupt or error
    pool.terminate()
    pool.join()
    if isinstance(e, KeyboardInterrupt):
        raise
```

When an interrupt occurs, we:
- Immediately terminate all worker processes
- Wait for them to finish with `join()`
- Re-raise the KeyboardInterrupt to propagate it up

### 3. Signal Handler in Main (`main.py`)
```python
def signal_handler(sig, frame):
    global interrupted
    interrupted = True
    print("\nInterrupt received. Cleaning up...")

signal.signal(signal.SIGINT, signal_handler)
```

This provides a custom handler that sets a flag and allows the program to finish its cleanup in the `finally` block.

### 4. Exception Handling in Main
```python
try:
    best_from_ga, progress = run_ga_lin_kernighan(...)
except KeyboardInterrupt:
    print("\nKeyboardInterrupt caught in main")
finally:
    # Save best solution found so far
    ...
```

Even if interrupted, the program will:
- Save the best solution found so far
- Print summary statistics
- Exit cleanly

## Testing

You can test the interrupt handling with the provided test script:
```bash
python test_interrupt.py
```

Then press Ctrl+C while it's running. You should see:
- "Interrupt received! Cleaning up..."
- Pool terminates immediately
- Program exits cleanly with final statistics

## Usage

The main program works exactly as before:
```bash
python main.py ..\EUCLIDEAN_200.txt output_E200.txt
```

But now you can press Ctrl+C at any time and it will:
1. Stop immediately (within ~1 second)
2. Save the best tour found so far
3. Print execution statistics
4. Exit cleanly without hanging

## Technical Details

The key insight is that on Windows with spawn:
- Child processes are completely separate
- They don't receive SIGINT by default
- The parent must explicitly terminate them
- Workers should ignore SIGINT to avoid race conditions

By having workers ignore SIGINT and handling termination in the parent process, we get clean, predictable shutdown behavior.
