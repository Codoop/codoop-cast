"""Maintainer entrypoint for the shared alignment runtime."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'runtime/codoop-cast'))
from castlib.alignment_engine import main, kept, subtitle_text, map_tokens, merge_zero_duration_units

if __name__ == '__main__':
    main()
