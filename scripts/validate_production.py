"""Compatibility launcher for the packaged contract validator."""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime/codoop-cast'))
from castlib.contracts import validate
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path)
    print(json.dumps(validate(parser.parse_args().package),ensure_ascii=False))
