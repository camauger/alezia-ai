"""Tests du matching de modèle de LLMService (résolution tolérante par préfixe)."""

from backend.services.llm_service import LLMService


class _FakeResp:
    status_code = 200

    def __init__(self, names):
        self._names = names

    def json(self):
        return {"models": [{"name": n} for n in self._names]}


def _service(monkeypatch, default_model, available):
    # importlib.import_module renvoie le vrai module (services/__init__ masque
    # le sous-module 'llm_service' par l'instance, donc `import ... as mod` ou
    # une cible string échouent). On patche requests.get AVANT de construire :
    # __init__ appelle check_model_availability() quand mock_mode défaut=False.
    import importlib

    mod = importlib.import_module("backend.services.llm_service")
    monkeypatch.setattr(mod.requests, "get", lambda *a, **k: _FakeResp(available))
    svc = LLMService()
    svc.default_model = default_model
    svc.mock_mode = True
    return svc


def test_exact_match_disables_mock(monkeypatch):
    svc = _service(monkeypatch, "gemma:2b", ["gemma:2b", "llama3.1:latest"])
    assert svc.check_model_availability() is True
    assert svc.mock_mode is False
    assert svc.default_model == "gemma:2b"


def test_prefix_match_resolves_versioned_tag(monkeypatch):
    # 'llama3' n'est pas installé tel quel, mais 'llama3.1:latest' l'est
    svc = _service(monkeypatch, "llama3", ["qwen2.5:7b", "llama3.1:latest"])
    assert svc.check_model_availability() is True
    assert svc.mock_mode is False
    assert svc.default_model == "llama3.1:latest"


def test_no_match_falls_back_to_mock(monkeypatch):
    svc = _service(monkeypatch, "mistral", ["gemma:2b", "llama3.1:latest"])
    assert svc.check_model_availability() is False
    assert svc.mock_mode is True
