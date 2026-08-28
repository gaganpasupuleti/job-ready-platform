from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.enums import PracticeMode, SessionStatus
from app.models.practice import PracticeAnswer, PracticeSession, PracticeSessionQuestion
from app.models.user import User
from app.repositories.practice_repository import PracticeRepository
from app.repositories.question_repository import QuestionRepository, TaxonomyRepository
from app.schemas.practice import (
    AnswerFeedback,
    AnswerOptionFeedback,
    AnswerRequest,
    AnswerResponse,
    CreateSessionRequest,
    HistoryItem,
    HistoryResponse,
    QuestionOptionPublic,
    QuestionPublic,
    QuestionReviewItem,
    SessionDetailResponse,
    SessionQuestionResponse,
    SessionResultsResponse,
    SessionSummary,
    TopicPerformance,
)


class PracticeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.practice_repo = PracticeRepository(db)
        self.question_repo = QuestionRepository(db)
        self.taxonomy_repo = TaxonomyRepository(db)

    async def create_session(self, user: User, payload: CreateSessionRequest) -> SessionDetailResponse:
        if not payload.category_id and not payload.topic_id:
            raise AppException("category_id or topic_id is required", status_code=400)

        questions = await self.question_repo.find_for_session(
            category_id=payload.category_id,
            topic_id=payload.topic_id,
            difficulty=payload.difficulty,
            limit=payload.question_count,
        )
        if not questions:
            raise AppException("No questions found for the selected filters", status_code=404)
        if len(questions) < payload.question_count:
            # Use available count
            pass

        domain_id = questions[0].domain_id
        category_id = payload.category_id or questions[0].category_id
        topic_id = payload.topic_id or questions[0].topic_id

        session = PracticeSession(
            user_id=user.id,
            mode=payload.mode,
            domain_id=domain_id,
            category_id=category_id,
            topic_id=topic_id,
            difficulty=payload.difficulty,
            question_count=len(questions),
            status=SessionStatus.ACTIVE,
            unanswered_count=len(questions),
        )
        session = await self.practice_repo.create_session(session)

        session_questions = [
            PracticeSessionQuestion(
                session_id=session.id,
                question_id=question.id,
                question_number=index + 1,
            )
            for index, question in enumerate(questions)
        ]
        await self.practice_repo.add_session_questions(session_questions)
        return self._session_detail(session, answered_count=0)

    async def get_session(self, user: User, session_id: UUID) -> SessionDetailResponse:
        session = await self._get_owned_session(user.id, session_id)
        answered_count = len([a for a in session.answers if a.answered_at is not None])
        return self._session_detail(session, answered_count=answered_count)

    async def get_question(
        self, user: User, session_id: UUID, question_number: int
    ) -> SessionQuestionResponse:
        session = await self._get_owned_session(user.id, session_id)
        sq = self._get_session_question(session, question_number)
        question = await self.question_repo.get_by_id(sq.question_id)
        if question is None:
            raise AppException("Question not found", status_code=404)

        topic_name = await self.question_repo.get_topic_name(question.topic_id)
        skills = await self.question_repo.get_skill_names(question.id)
        answered = await self.practice_repo.get_answer(session.id, question.id)
        bookmarked = await self.practice_repo.is_bookmarked(user.id, question.id)

        return SessionQuestionResponse(
            question_number=question_number,
            total_questions=session.question_count,
            question=self._public_question(question, topic_name, skills),
            answered=answered is not None and answered.answered_at is not None,
            bookmarked=bookmarked,
        )

    async def submit_answer(
        self,
        user: User,
        session_id: UUID,
        question_number: int,
        payload: AnswerRequest,
    ) -> AnswerResponse:
        session = await self._get_owned_session(user.id, session_id)
        if session.status != SessionStatus.ACTIVE:
            raise AppException("Session is not active", status_code=400)

        sq = self._get_session_question(session, question_number)
        question = await self.question_repo.get_by_id(sq.question_id)
        if question is None:
            raise AppException("Question not found", status_code=404)

        existing = await self.practice_repo.get_answer(session.id, question.id)
        if existing and existing.answered_at is not None:
            raise AppException("Question already answered", status_code=400)

        selected_ids = [str(option_id) for option_id in payload.selected_option_ids]
        is_correct, marks_awarded = self._evaluate_answer(question, payload.selected_option_ids)

        answer = existing or PracticeAnswer(session_id=session.id, question_id=question.id)
        answer.selected_option_ids = selected_ids
        answer.is_correct = is_correct
        answer.marks_awarded = marks_awarded
        answer.time_spent_seconds = payload.time_spent_seconds
        answer.answered_at = datetime.now(UTC)
        await self.practice_repo.save_answer(answer)

        await self._refresh_session_counts(session)

        feedback = None
        if session.mode == PracticeMode.PRACTICE:
            topic_name = await self.question_repo.get_topic_name(question.topic_id)
            skills = await self.question_repo.get_skill_names(question.id)
            feedback = AnswerFeedback(
                is_correct=is_correct,
                marks_awarded=marks_awarded,
                correct_option_ids=[opt.id for opt in question.options if opt.is_correct],
                selected_option_ids=payload.selected_option_ids,
                explanation=question.explanation,
                options=[
                    AnswerOptionFeedback(
                        id=opt.id,
                        option_text=opt.option_text,
                        is_correct=opt.is_correct,
                    )
                    for opt in question.options
                ],
                topic_name=topic_name,
                difficulty=question.difficulty,
                skills=skills,
                reveal_feedback=True,
            )

        return AnswerResponse(
            question_number=question_number,
            answered=True,
            feedback=feedback,
        )

    async def complete_session(self, user: User, session_id: UUID) -> SessionResultsResponse:
        session = await self._get_owned_session(user.id, session_id)
        if session.status == SessionStatus.COMPLETED:
            return await self.get_results(user, session_id)

        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.now(UTC)
        await self._refresh_session_counts(session)
        await self.practice_repo.save_session(session)
        return await self.get_results(user, session_id)

    async def get_results(self, user: User, session_id: UUID) -> SessionResultsResponse:
        session = await self._get_owned_session(user.id, session_id)
        if session.mode == PracticeMode.EXAM and session.status != SessionStatus.COMPLETED:
            raise AppException("Complete the exam before viewing results", status_code=400)

        reviews: list[QuestionReviewItem] = []
        topic_stats: dict[str, dict[str, int]] = {}
        total_time = 0

        for sq in sorted(session.questions, key=lambda item: item.question_number):
            question = await self.question_repo.get_by_id(sq.question_id)
            if question is None:
                continue
            answer = await self.practice_repo.get_answer(session.id, question.id)
            correct_ids = [opt.id for opt in question.options if opt.is_correct]
            selected_ids = []
            selected_texts = []
            if answer and answer.selected_option_ids:
                selected_ids = [UUID(value) for value in answer.selected_option_ids]
                selected_texts = [
                    opt.option_text
                    for opt in question.options
                    if str(opt.id) in answer.selected_option_ids
                ]
            correct_texts = [opt.option_text for opt in question.options if opt.is_correct]
            topic_name = await self.question_repo.get_topic_name(question.topic_id) or "General"
            stats = topic_stats.setdefault(topic_name, {"total": 0, "correct": 0})
            stats["total"] += 1
            is_correct = bool(answer and answer.is_correct)
            if is_correct:
                stats["correct"] += 1
            if answer:
                total_time += answer.time_spent_seconds

            reviews.append(
                QuestionReviewItem(
                    question_number=sq.question_number,
                    question_text=question.question_text,
                    selected_option_ids=selected_ids,
                    correct_option_ids=correct_ids,
                    selected_option_texts=selected_texts,
                    correct_option_texts=correct_texts,
                    explanation=question.explanation,
                    is_correct=is_correct,
                    marks_awarded=answer.marks_awarded if answer else 0.0,
                )
            )

        accuracy = (
            round((session.correct_count / session.question_count) * 100, 2)
            if session.question_count
            else 0.0
        )
        return SessionResultsResponse(
            session=self._session_summary(session),
            accuracy=accuracy,
            time_taken_seconds=total_time,
            topic_performance=[
                TopicPerformance(
                    topic_name=name,
                    accuracy=round((values["correct"] / values["total"]) * 100, 2),
                    total=values["total"],
                    correct=values["correct"],
                )
                for name, values in topic_stats.items()
            ],
            questions=reviews,
        )

    async def get_history(self, user: User) -> HistoryResponse:
        sessions = await self.practice_repo.list_history(user.id)
        items: list[HistoryItem] = []
        for session in sessions:
            category_name = None
            topic_name = None
            if session.category_id:
                category = await self.taxonomy_repo.get_category(session.category_id)
                category_name = category.name if category else None
            if session.topic_id:
                topic = await self.taxonomy_repo.get_topic(session.topic_id)
                topic_name = topic.name if topic else None
            items.append(
                HistoryItem(
                    id=session.id,
                    mode=session.mode,
                    status=session.status.value,
                    question_count=session.question_count,
                    score=session.score,
                    correct_count=session.correct_count,
                    incorrect_count=session.incorrect_count,
                    started_at=session.started_at.isoformat(),
                    completed_at=session.completed_at.isoformat() if session.completed_at else None,
                    category_name=category_name,
                    topic_name=topic_name,
                )
            )
        return HistoryResponse(sessions=items)

    async def toggle_bookmark(self, user: User, question_id: UUID) -> dict[str, bool]:
        question = await self.question_repo.get_by_id(question_id)
        if question is None:
            raise AppException("Question not found", status_code=404)
        bookmarked = await self.practice_repo.toggle_bookmark(user.id, question_id)
        return {"bookmarked": bookmarked}

    async def _get_owned_session(self, user_id: UUID, session_id: UUID) -> PracticeSession:
        session = await self.practice_repo.get_session_for_user(session_id, user_id)
        if session is None:
            raise AppException("Session not found", status_code=404)
        return session

    def _get_session_question(
        self, session: PracticeSession, question_number: int
    ) -> PracticeSessionQuestion:
        for sq in session.questions:
            if sq.question_number == question_number:
                return sq
        raise AppException("Question number out of range", status_code=404)

    def _public_question(
        self, question, topic_name: str | None, skills: list[str]
    ) -> QuestionPublic:
        return QuestionPublic(
            id=question.id,
            question_type=question.question_type,
            title=question.title,
            question_text=question.question_text,
            difficulty=question.difficulty,
            marks=question.marks,
            negative_marks=question.negative_marks,
            estimated_time_seconds=question.estimated_time_seconds,
            options=[
                QuestionOptionPublic(
                    id=opt.id,
                    option_text=opt.option_text,
                    sort_order=opt.sort_order,
                )
                for opt in question.options
            ],
            topic_name=topic_name,
            skills=skills,
        )

    def _evaluate_answer(self, question, selected_option_ids: list[UUID]) -> tuple[bool, float]:
        correct_ids = {opt.id for opt in question.options if opt.is_correct}
        selected_set = set(selected_option_ids)
        if not selected_set and question.question_type.value != "true_false":
            return False, 0.0
        is_correct = selected_set == correct_ids and len(correct_ids) > 0
        if is_correct:
            return True, question.marks
        if selected_set and question.negative_marks > 0:
            return False, -question.negative_marks
        return False, 0.0

    async def _refresh_session_counts(self, session: PracticeSession) -> None:
        session = await self.practice_repo.get_session_for_user(session.id, session.user_id)
        if session is None:
            return
        answers = [a for a in session.answers if a.answered_at is not None]
        correct = len([a for a in answers if a.is_correct])
        incorrect = len([a for a in answers if a.is_correct is False])
        unanswered = session.question_count - len(answers)
        session.correct_count = correct
        session.incorrect_count = incorrect
        session.unanswered_count = unanswered
        session.score = sum(a.marks_awarded for a in answers)
        await self.practice_repo.save_session(session)

    def _session_summary(self, session: PracticeSession) -> SessionSummary:
        return SessionSummary(
            id=session.id,
            mode=session.mode,
            status=session.status.value,
            question_count=session.question_count,
            score=session.score,
            correct_count=session.correct_count,
            incorrect_count=session.incorrect_count,
            unanswered_count=session.unanswered_count,
            started_at=session.started_at.isoformat(),
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
        )

    def _session_detail(self, session: PracticeSession, answered_count: int) -> SessionDetailResponse:
        summary = self._session_summary(session)
        return SessionDetailResponse(
            **summary.model_dump(),
            category_id=session.category_id,
            topic_id=session.topic_id,
            difficulty=session.difficulty,
            answered_count=answered_count,
        )
