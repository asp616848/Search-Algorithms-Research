import subprocess
import os
import sys
import time
import signal
from pathlib import Path

# This runner is designed to be executed from the repository root or the code/ folder.
# It will use the Python executable inside the venv at ./venv/bin/python by default.


def find_venv_python(venv_path: Path) -> str:
    py = venv_path / 'bin' / 'python'
    if py.exists():
        return str(py)
    raise FileNotFoundError(f"Python executable not found in venv: {py}")


def last_tour_from_file(path: Path):
    if not path.exists():
        return None
    try:
        with path.open('r', encoding='utf-8', errors='ignore') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if not lines:
            return None
        last = lines[-1]
        tour = list(map(int, last.split()))
        return tour
    except Exception:
        return None


def compute_cost_from_tour(tour, dist_matrix):
    # lightweight re-use of utils.compute_cost logic without import cycles
    import numpy as _np
    if tour is None:
        return None
    t = _np.asarray(tour, dtype=int)
    if t.size == 0:
        return 0.0
    next_idx = _np.roll(t, -1)
    return float(dist_matrix[t, next_idx].sum())


def main():
    # base paths
    repo_root = Path(__file__).resolve().parent
    # code folder is repo_root
    code_dir = repo_root

    # default venv location relative to project root (as provided by user)
    # user indicated venv at: /home/abhi/College/SMAI/venv
    # We'll attempt to use that, otherwise fallback to ./venv
    possible_venvs = [Path('/home/abhi/College/SMAI/venv'), repo_root / 'venv', repo_root.parent / 'venv']
    venv_python = None
    for vp in possible_venvs:
        try:
            venv_python = find_venv_python(vp)
            break
        except FileNotFoundError:
            continue

    if venv_python is None:
        print('Could not locate venv python automatically. Please set VENV_PYTHON env var to the python executable inside your venv.')
        venv_python = os.environ.get('VENV_PYTHON')
        if not venv_python:
            sys.exit(1)

    main_py = str(code_dir / 'main.py')

    tests = [
        (str(code_dir / '..' / 'EUCLIDEAN_50.txt'), str(code_dir / 'a/output_E50.txt')),
        (str(code_dir / '..' / 'EUCLIDEAN_100.txt'), str(code_dir / 'a/output_E100.txt')),
        (str(code_dir / '..' / 'EUCLIDEAN_200.txt'), str(code_dir / 'a/output_E200.txt')),
        (str(code_dir / '..' / 'NON_EUCLIDEAN_50.txt'), str(code_dir / 'a/output_NE50.txt')),
        (str(code_dir / '..' / 'NON_EUCLIDEAN_100.txt'), str(code_dir / 'a/output_NE100.txt')),
        (str(code_dir / '..' / 'NON_EUCLIDEAN_200.txt'), str(code_dir / 'a/output_NE200.txt')),
    ]

    TIMEOUT = int(os.environ.get('RUN_TIMEOUT', '300'))

    summary_lines = []

    # ensure outputs directory exists (we'll keep outputs in code dir)
    # run each job sequentially
    for inp, outp in tests:
        inp_p = Path(inp).resolve()
        out_p = Path(outp).resolve()

        # clear output file before run
        try:
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text('')
        except Exception as e:
            print(f'Warning: could not clear {out_p}: {e}')

        cmd = [venv_python, main_py, str(inp_p), str(out_p), str(TIMEOUT)]
        print(f'Running: {cmd}')

        start = time.time()
        try:
            proc = subprocess.Popen(cmd)
            proc.wait(timeout=TIMEOUT)
            retcode = proc.returncode
            status = 'finished' if retcode == 0 else f'exited({retcode})'
        except subprocess.TimeoutExpired:
            # First, try to terminate gracefully with SIGTERM
            print(f"Timeout reached for {inp_p.name}, sending SIGTERM...")
            proc.terminate()
            try:
                # Wait up to 5 seconds for graceful shutdown
                proc.wait(timeout=5)
                status = 'timeout-terminated'
            except subprocess.TimeoutExpired:
                # If still running, force kill
                print(f"Process didn't terminate gracefully, sending SIGKILL...")
                proc.kill()
                proc.wait()
                status = 'timeout-killed'
        except FileNotFoundError as e:
            status = f'file-not-found: {e}'
        except Exception as e:
            status = f'error: {e}'
        end = time.time()
        elapsed = end - start

        # load input matrix to compute cost
        try:
            from utils import read_input
            metric, n, dist_matrix = read_input(str(inp_p))
        except Exception as e:
            print(f'Could not read input {inp_p}: {e}')
            dist_matrix = None

        last_tour = last_tour_from_file(out_p)
        if dist_matrix is not None and last_tour is not None:
            cost = compute_cost_from_tour(last_tour, dist_matrix)
            cost_str = f'{cost:.6f}'
        else:
            cost_str = 'N/A'

        line = f"{inp_p.name}: status={status}, time={elapsed:.2f}s, last_cost={cost_str}"
        print(line)
        summary_lines.append(line)

    # write summary to file in code dir
    summary_file = code_dir / 'summary_output.txt'
    try:
        summary_file.write_text('\n'.join(summary_lines) + '\n')
        print(f'Summary written to {summary_file}')
    except Exception as e:
        print(f'Could not write summary file: {e}')


if __name__ == '__main__':
    main()
