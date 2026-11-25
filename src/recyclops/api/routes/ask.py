"""POST /api/ask: "Can we...?" for one member and one activity. The AI may read the question; code answers it."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends

from recyclops.ai.ask import QuestionReader
from recyclops.ai.templates import decision_why
from recyclops.api.dependencies import get_air_provider, get_question_reader, today_in_india
from recyclops.api.schemas import VERDICTS, AirOut, AskedOut, AskOut, AskRequest, DecisionOut
from recyclops.data.models import AirProvider
from recyclops.domain.forecast import day_windows
from recyclops.domain.plan import decide

router = APIRouter()


@router.post("/api/ask")
async def ask(
    request: AskRequest,
    provider: AirProvider = Depends(get_air_provider),
    reader: QuestionReader = Depends(get_question_reader),
    today: date = Depends(today_in_india),
) -> AskOut:
    snapshot = await provider.snapshot(request.location.lat, request.location.lon)
    air = AirOut.of(snapshot)
    household = request.household

    if request.form:
        member_id, day_word, activity, ai_used = request.form.member_id, request.form.day, request.form.activity, False
    else:
        parse = await reader.read(request.question or "", household)
        if parse is None or (asked := parse.asked()) is None:
            return AskOut(air=air, needs_form=True, ai_used=parse is not None)
        (member_id, activity), day_word, ai_used = asked, parse.day, True

    member = next(m for m in household.members if m.id == member_id)
    day = today + timedelta(days=1 if day_word == "tomorrow" else 0)
    windows = day_windows(snapshot.forecast, day)
    decision = decide(member, activity, household.home, snapshot.forecast, windows, day)
    why = decision_why(decision, windows.best.band if windows else None)
    return AskOut(
        air=air, needs_form=False, ai_used=ai_used,
        asked=AskedOut(member_id=member.id, name=member.name, day=day, activity=activity),
        verdict=VERDICTS[decision.action],
        decision=DecisionOut.of(decision, why, household.home.has_purifier),
    )
