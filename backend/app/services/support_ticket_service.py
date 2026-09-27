import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.support_ticket import SupportTicket, SupportTicketMessage, SupportTicketStatusEvent
from app.models.user import User
from app.schemas.support_ticket import (
    AdminSupportTicketDetail,
    AdminSupportTicketSummary,
    SupportReplyCreate,
    SupportStatusUpdate,
    SupportTicketCreate,
    SupportTicketDetail,
    SupportTicketSummary,
    SupportTimelineItem,
)

HOURLY_TICKET_LIMIT = 10
HOURLY_REPLY_LIMIT = 30


def _name(user: User) -> str:
    return (user.full_name or "").strip() or user.username


def _role(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


class SupportTicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(self, user: User, payload: SupportTicketCreate) -> SupportTicketDetail:
        existing = await self._ticket_for_request(user.id, payload.client_request_id)
        if existing is not None:
            self._assert_same_create(existing, payload)
            return await self.student_detail(user, existing.id)

        await self._enforce_ticket_limit(user.id)
        ticket = SupportTicket(
            user_id=user.id,
            reference=await self._new_reference(),
            category=payload.category,
            title=payload.title,
            description=payload.description,
            page_path=payload.page_path,
            status="new",
            client_request_id=payload.client_request_id,
        )
        self.db.add(ticket)
        await self.db.flush()
        ticket_id = ticket.id
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            existing = await self._ticket_for_request(user.id, payload.client_request_id)
            if existing is None:
                raise AppException("Could not save this request. Try again.", status_code=409) from None
            self._assert_same_create(existing, payload)
            return await self.student_detail(user, existing.id)
        self.db.expire(ticket)
        return await self.student_detail(user, ticket_id)

    async def list_for_student(self, user: User) -> list[SupportTicketSummary]:
        rows = (
            await self.db.scalars(
                select(SupportTicket)
                .where(SupportTicket.user_id == user.id)
                .order_by(SupportTicket.created_at.desc())
                .limit(50)
            )
        ).all()
        return [self._summary(row) for row in rows]

    async def student_detail(self, user: User, ticket_id: uuid.UUID) -> SupportTicketDetail:
        ticket = await self._owned(user, ticket_id)
        return self._detail(ticket)

    async def add_student_reply(
        self,
        user: User,
        ticket_id: uuid.UUID,
        payload: SupportReplyCreate,
    ) -> SupportTicketDetail:
        ticket = await self._owned(user, ticket_id)
        await self._add_reply(ticket, user, payload)
        return await self.student_detail(user, ticket_id)

    async def admin_list(
        self,
        *,
        category: str | None,
        status: str | None,
        date_from: date | None,
        date_to: date | None,
    ) -> list[AdminSupportTicketSummary]:
        if date_from and date_to and date_from > date_to:
            raise AppException("The start date must be on or before the end date", status_code=400)
        stmt = select(SupportTicket).options(selectinload(SupportTicket.user)).order_by(SupportTicket.created_at.desc())
        if category:
            stmt = stmt.where(SupportTicket.category == category)
        if status:
            stmt = stmt.where(SupportTicket.status == status)
        if date_from:
            stmt = stmt.where(SupportTicket.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
        if date_to:
            stmt = stmt.where(
                SupportTicket.created_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
            )
        rows = (await self.db.scalars(stmt.limit(100))).all()
        return [self._admin_summary(row) for row in rows]

    async def admin_detail(self, ticket_id: uuid.UUID) -> AdminSupportTicketDetail:
        ticket = await self._loaded(ticket_id)
        if ticket is None:
            raise AppException("Request not found", status_code=404)
        return self._admin_detail(ticket)

    async def add_admin_reply(
        self,
        actor: User,
        ticket_id: uuid.UUID,
        payload: SupportReplyCreate,
    ) -> AdminSupportTicketDetail:
        ticket = await self._loaded(ticket_id)
        if ticket is None:
            raise AppException("Request not found", status_code=404)
        await self._add_reply(ticket, actor, payload)
        return await self.admin_detail(ticket_id)

    async def change_status(
        self,
        actor: User,
        ticket_id: uuid.UUID,
        payload: SupportStatusUpdate,
    ) -> AdminSupportTicketDetail:
        ticket = await self._loaded(ticket_id)
        if ticket is None:
            raise AppException("Request not found", status_code=404)
        existing = await self._status_for_request(ticket.id, payload.client_request_id)
        if existing is not None:
            if existing.to_status != payload.status:
                raise AppException("This status update was already sent with a different status", status_code=409)
            return self._admin_detail(ticket)
        if ticket.status == payload.status:
            return self._admin_detail(ticket)

        event = SupportTicketStatusEvent(
            ticket_id=ticket.id,
            actor_id=actor.id,
            actor_name=_name(actor),
            actor_role=_role(actor),
            from_status=ticket.status,
            to_status=payload.status,
            client_request_id=payload.client_request_id,
        )
        ticket.status = payload.status
        ticket.updated_at = datetime.now(timezone.utc)
        self.db.add(event)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            existing = await self._status_for_request(ticket_id, payload.client_request_id)
            if existing is None or existing.to_status != payload.status:
                raise AppException("Could not update the status. Try again.", status_code=409) from None
        self.db.expire(ticket)
        return await self.admin_detail(ticket_id)

    async def _add_reply(self, ticket: SupportTicket, author: User, payload: SupportReplyCreate) -> None:
        existing = await self._message_for_request(ticket.id, payload.client_request_id)
        if existing is not None:
            if existing.body != payload.body:
                raise AppException("This reply was already sent with different text", status_code=409)
            return
        await self._enforce_reply_limit(author.id)
        message = SupportTicketMessage(
            ticket_id=ticket.id,
            author_id=author.id,
            author_name=_name(author),
            author_role=_role(author),
            body=payload.body,
            client_request_id=payload.client_request_id,
        )
        ticket.updated_at = datetime.now(timezone.utc)
        self.db.add(message)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            existing = await self._message_for_request(ticket.id, payload.client_request_id)
            if existing is None or existing.body != payload.body:
                raise AppException("Could not save this reply. Try again.", status_code=409) from None
        self.db.expire(ticket)

    async def _enforce_ticket_limit(self, user_id: uuid.UUID) -> None:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        count = await self.db.scalar(
            select(func.count())
            .select_from(SupportTicket)
            .where(SupportTicket.user_id == user_id, SupportTicket.created_at >= since)
        )
        if (count or 0) >= HOURLY_TICKET_LIMIT:
            raise AppException(
                "You have sent several requests recently. Please wait before sending another.",
                status_code=429,
            )

    async def _enforce_reply_limit(self, user_id: uuid.UUID) -> None:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        count = await self.db.scalar(
            select(func.count())
            .select_from(SupportTicketMessage)
            .where(SupportTicketMessage.author_id == user_id, SupportTicketMessage.created_at >= since)
        )
        if (count or 0) >= HOURLY_REPLY_LIMIT:
            raise AppException("You have sent several replies recently. Please wait a moment.", status_code=429)

    async def _owned(self, user: User, ticket_id: uuid.UUID) -> SupportTicket:
        ticket = await self._loaded(ticket_id)
        if ticket is None or ticket.user_id != user.id:
            raise AppException("Request not found", status_code=404)
        return ticket

    async def _loaded(self, ticket_id: uuid.UUID) -> SupportTicket | None:
        return await self.db.scalar(
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .options(
                selectinload(SupportTicket.messages),
                selectinload(SupportTicket.status_events),
                selectinload(SupportTicket.user),
            )
        )

    async def _ticket_for_request(self, user_id: uuid.UUID, request_id: str) -> SupportTicket | None:
        return await self.db.scalar(
            select(SupportTicket).where(
                SupportTicket.user_id == user_id,
                SupportTicket.client_request_id == request_id,
            )
        )

    async def _message_for_request(self, ticket_id: uuid.UUID, request_id: str) -> SupportTicketMessage | None:
        return await self.db.scalar(
            select(SupportTicketMessage).where(
                SupportTicketMessage.ticket_id == ticket_id,
                SupportTicketMessage.client_request_id == request_id,
            )
        )

    async def _status_for_request(self, ticket_id: uuid.UUID, request_id: str) -> SupportTicketStatusEvent | None:
        return await self.db.scalar(
            select(SupportTicketStatusEvent).where(
                SupportTicketStatusEvent.ticket_id == ticket_id,
                SupportTicketStatusEvent.client_request_id == request_id,
            )
        )

    async def _new_reference(self) -> str:
        for _ in range(5):
            reference = f"SF-{secrets.token_hex(4).upper()}"
            taken = await self.db.scalar(select(SupportTicket.id).where(SupportTicket.reference == reference))
            if taken is None:
                return reference
        raise AppException("Could not assign a ticket reference. Try again.", status_code=503)

    def _assert_same_create(self, ticket: SupportTicket, payload: SupportTicketCreate) -> None:
        same = (
            ticket.category == payload.category
            and ticket.title == payload.title
            and ticket.description == payload.description
            and ticket.page_path == payload.page_path
        )
        if not same:
            raise AppException("This request was already sent with different details", status_code=409)

    def _summary(self, ticket: SupportTicket) -> SupportTicketSummary:
        return SupportTicketSummary(
            id=ticket.id,
            reference=ticket.reference,
            category=ticket.category,
            title=ticket.title,
            status=ticket.status,
            page_path=ticket.page_path,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

    def _detail(self, ticket: SupportTicket) -> SupportTicketDetail:
        return SupportTicketDetail(**self._summary(ticket).model_dump(), description=ticket.description, timeline=self._timeline(ticket))

    def _admin_summary(self, ticket: SupportTicket) -> AdminSupportTicketSummary:
        student = ticket.user
        return AdminSupportTicketSummary(
            **self._summary(ticket).model_dump(),
            student_name=_name(student),
            student_email=student.email,
        )

    def _admin_detail(self, ticket: SupportTicket) -> AdminSupportTicketDetail:
        summary = self._admin_summary(ticket)
        return AdminSupportTicketDetail(**summary.model_dump(), description=ticket.description, timeline=self._timeline(ticket))

    def _timeline(self, ticket: SupportTicket) -> list[SupportTimelineItem]:
        items: list[SupportTimelineItem] = []
        for message in ticket.messages:
            items.append(
                SupportTimelineItem(
                    id=message.id,
                    kind="reply",
                    author_name=message.author_name,
                    author_role=message.author_role,
                    body=message.body,
                    created_at=message.created_at,
                )
            )
        for event in ticket.status_events:
            items.append(
                SupportTimelineItem(
                    id=event.id,
                    kind="status",
                    author_name=event.actor_name,
                    author_role=event.actor_role,
                    from_status=event.from_status,
                    to_status=event.to_status,
                    created_at=event.created_at,
                )
            )
        items.sort(key=lambda item: item.created_at)
        return items
