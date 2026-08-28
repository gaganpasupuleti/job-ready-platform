import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Domain(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "domains"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    categories: Mapped[list["Category"]] = relationship(back_populates="domain")


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("domain_id", "slug", name="uq_category_domain_slug"),)

    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    domain: Mapped["Domain"] = relationship(back_populates="categories")
    topics: Mapped[list["Topic"]] = relationship(back_populates="category")


class Topic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("category_id", "slug", name="uq_topic_category_slug"),)

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="topics")
    subtopics: Mapped[list["Subtopic"]] = relationship(back_populates="topic")


class Subtopic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subtopics"
    __table_args__ = (UniqueConstraint("topic_id", "slug", name="uq_subtopic_topic_slug"),)

    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    topic: Mapped["Topic"] = relationship(back_populates="subtopics")
