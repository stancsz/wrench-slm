import subprocess
import sys

import psutil

from scripts.verify_weight_package import process_tree_rss, stop_process_tree


def test_memory_sampler_counts_interpreter_descendants():
    worker = "import time; data=bytearray(64*1024*1024); print('ready', flush=True); time.sleep(5)"
    parent = "import subprocess,sys; subprocess.run([sys.executable, '-c', sys.argv[1]], check=True)"
    child = subprocess.Popen([sys.executable, '-c', parent, worker], stdout=subprocess.PIPE, text=True)
    process = psutil.Process(child.pid)
    try:
        assert child.stdout.readline().strip() == 'ready'
        assert process_tree_rss(process) >= 64 * 1024 * 1024
        assert process.children(recursive=True)
    finally:
        stop_process_tree(process)
        child.wait(timeout=10)
