import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import kubernetes_monitoring


def test_main_function_exists():
    """Test that main function exists and is callable"""
    assert callable(kubernetes_monitoring.main)


def test_node_group_label_constant():
    """Test that NODE_GROUP_LABEL constant is defined"""
    assert hasattr(kubernetes_monitoring, "NODE_GROUP_LABEL")
    assert isinstance(kubernetes_monitoring.NODE_GROUP_LABEL, str)


@patch("kubernetes_monitoring.config")
def test_load_kube_config_success(mock_config):
    """Test successful kube config loading"""
    mock_config.load_kube_config.return_value = None

    # Should not raise an exception
    kubernetes_monitoring.load_kube_config()
    mock_config.load_kube_config.assert_called_once()


@patch("kubernetes_monitoring.config")
@patch("sys.exit")
def test_load_kube_config_failure(mock_exit, mock_config):
    """Test kube config loading failure"""
    mock_config.load_kube_config.side_effect = Exception("Config error")

    kubernetes_monitoring.load_kube_config()
    mock_exit.assert_called_once_with(1)


@patch("kubernetes_monitoring.Prompt.ask")
@patch("kubernetes_monitoring.client")
@patch("kubernetes_monitoring.load_kube_config")
def test_choose_namespace_success(mock_load_config, mock_client, mock_prompt):
    """Test successful namespace selection"""
    # Mock the namespace list
    mock_ns = MagicMock()
    mock_ns.metadata.name = "test-namespace"

    mock_ns_list = MagicMock()
    mock_ns_list.items = [mock_ns]

    mock_v1 = MagicMock()
    mock_v1.list_namespace.return_value = mock_ns_list
    mock_client.CoreV1Api.return_value = mock_v1

    # Mock user input (empty string for default/all namespaces)
    mock_prompt.return_value = ""

    # This should not raise an exception
    kubernetes_monitoring.choose_namespace()
    mock_load_config.assert_called_once()


@patch("kubernetes_monitoring.client")
@patch("kubernetes_monitoring.load_kube_config")
def test_choose_namespace_failure(mock_load_config, mock_client):
    """Test namespace selection failure"""
    mock_v1 = MagicMock()
    mock_v1.list_namespace.side_effect = Exception("API error")
    mock_client.CoreV1Api.return_value = mock_v1

    kubernetes_monitoring.choose_namespace()
    assert mock_load_config.called
