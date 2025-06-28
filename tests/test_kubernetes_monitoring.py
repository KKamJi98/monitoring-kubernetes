import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import kubernetes_monitoring


def test_main_function_exists():
    assert callable(kubernetes_monitoring.main)
