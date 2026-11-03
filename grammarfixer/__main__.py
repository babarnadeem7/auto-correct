import os
import sys

# Allow `python grammarfixer/__main__.py` (used by autostart and PyInstaller)
# in addition to `python -m grammarfixer`.
if not __package__:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grammarfixer.app import main

if __name__ == "__main__":
    main()
