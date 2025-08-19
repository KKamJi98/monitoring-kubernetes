import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import kubernetes_monitoring  # noqa: E402


@patch("kubernetes_monitoring.cleanup")
@patch("sys.exit")
def test_keyboard_interrupt_graceful_exit(mock_exit, mock_cleanup):
    # main_menu 호출 시 KeyboardInterrupt 발생을 시뮬레이션
    with patch("kubernetes_monitoring.main_menu", side_effect=KeyboardInterrupt):
        kubernetes_monitoring.main()

    mock_cleanup.assert_called_once()
    mock_exit.assert_called_once_with(130)


@patch("kubernetes_monitoring.cleanup")
@patch("sys.exit")
def test_eoferror_graceful_exit(mock_exit, mock_cleanup):
    # main_menu 호출 시 EOFError 발생을 시뮬레이션
    with patch("kubernetes_monitoring.main_menu", side_effect=EOFError):
        kubernetes_monitoring.main()

    mock_cleanup.assert_called_once()
    mock_exit.assert_called_once_with(0)
