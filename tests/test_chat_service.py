"""Round-trip du service de chat sur une base temporaire isolée."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.character import CharacterModel
from backend.models.memory import MemoryModel


@pytest.fixture
def chat_service_isolated(tmp_path, monkeypatch):
    # Importer chat_service AVANT create_all : son import enregistre les
    # modèles ORM du chat (chat_sessions/chat_messages) dans Base.metadata.
    import backend.services.chat_service as cs
    from backend import models  # noqa: F401  (enregistre les autres tables)

    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    test_sessionmaker = sessionmaker(bind=engine)

    seed = test_sessionmaker()
    seed.add(
        CharacterModel(
            id=999,
            name="Testeur",
            description="Un personnage de test pour les tests unitaires.",
            personality="Calme, curieux et serviable envers tous.",
        )
    )
    seed.commit()
    seed.close()

    # Router toutes les sessions de chat_service vers la base temporaire.
    monkeypatch.setattr(cs, "SessionLocal", test_sessionmaker)
    return cs.chat_service, test_sessionmaker


def test_create_session_and_send_message_roundtrip(chat_service_isolated):
    chat, test_sessionmaker = chat_service_isolated

    session = chat.create_session(user_id="u1", character_id=999, context=None)
    assert isinstance(session["id"], str)

    response = chat.send_message(
        session_id=session["id"], user_input="Bonjour", metadata=None
    )
    assert response["sender"] == "assistant"
    assert response["content"]

    messages = chat.get_session_messages(session["id"])
    senders = [m["sender"] for m in messages]
    assert "user" in senders and "assistant" in senders

    # Vérifier qu'une mémoire a bien été persistée pour ce personnage
    session_db = test_sessionmaker()
    try:
        count = session_db.query(MemoryModel).filter_by(character_id=999).count()
        assert count >= 1, f"Aucune mémoire persistée pour character_id=999 (count={count})"
    finally:
        session_db.close()
