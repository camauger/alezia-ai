"""Round-trip ORM des modèles de chat sur une base SQLite en mémoire."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.chat import ChatSessionModel, MessageModel


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_chat_session_uses_string_uuid_id():
    db = _session()
    sid = str(uuid.uuid4())
    db.add(ChatSessionModel(id=sid, user_id="u1", character_id=1, active=True))
    db.commit()
    row = db.query(ChatSessionModel).filter_by(id=sid).first()
    assert row is not None
    assert row.id == sid
    assert row.active is True


def test_message_links_to_session():
    db = _session()
    sid = str(uuid.uuid4())
    mid = str(uuid.uuid4())
    db.add(ChatSessionModel(id=sid, user_id="u1", character_id=1))
    db.add(MessageModel(id=mid, session_id=sid, sender="user", content="bonjour"))
    db.commit()
    msg = db.query(MessageModel).filter_by(id=mid).first()
    assert msg.session_id == sid
    assert msg.sender == "user"
    assert msg.content == "bonjour"
