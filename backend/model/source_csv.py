from datetime import datetime
from uuid import uuid4

from core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class SourceCSV(Base):
    __tablename__ = "source_csv"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    migrations = relationship("Migration", back_populates="source_csv")
