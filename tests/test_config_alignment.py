"""Vérifie que la config unique expose les clés attendues par llm_service."""

from backend import config


def test_llm_config_has_keys_read_by_llm_service():
    for key in ("api_url", "default_model", "mock_mode", "temperature", "max_tokens"):
        assert key in config.LLM_CONFIG, f"Clé manquante dans LLM_CONFIG: {key}"


def test_llm_mock_mode_defaults_to_false():
    assert config.LLM_CONFIG["mock_mode"] is False


def test_root_config_is_gone():
    from pathlib import Path

    root_config = Path(__file__).resolve().parent.parent / "config.py"
    assert not root_config.exists(), "Le config.py racine doit être supprimé"
