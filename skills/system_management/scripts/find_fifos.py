#!/usr/bin/env python3
import os
import stat

def find_fifos(path='/tmp'):
    fifos = []
    try:
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if stat.S_ISFIFO(os.stat(full_path).st_mode):
                fifos.append(f)
    except Exception as e:
        return [str(e)]
    return fifos

if __name__ == "__main__":
    print(find_fifos())
