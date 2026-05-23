"""Study plan: AI-generated weekly plan based on exam date."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, openai_client, get_current_user
from models import StudyPlanRequest

router = APIRouter()


@router.post("/study-plan")
async def create_study_plan(body: StudyPlanRequest, request: Request):
    user = await get_current_user(request)
    try:
        exam_dt = datetime.fromisoformat(body.exam_date.replace("Z", "+00:00"))
        days_until = max(1, (exam_dt.replace(tzinfo=None) - datetime.now()).days)
    except Exception:
        days_until = 30

    weeks = max(1, days_until // 7)
    subjects_str = ', '.join(body.subjects) if body.subjects else 'All subjects'
    prompt = f"""Create a CBSE exam study plan. Class {body.class_level}, {days_until} days left, target {body.target_score}%, {body.daily_hours}h/day, subjects: {subjects_str}.
Return JSON only:
{{"overview":"2-line strategy","weeks":[{{"week":1,"theme":"Foundation","focus":["topic1"],"daily_tasks":[{{"day":"Mon","subject":"...","topic":"...","hours":2,"type":"learn"}}],"goal":"..."}}],"exam_week":"strategy","tips":["tip1","tip2","tip3"]}}
Max {weeks} weeks. Prioritize high-weightage topics. Be specific and actionable."""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}, temperature=0.7, max_tokens=2500,
        )
        plan_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Study plan generation failed: {e}")

    now = datetime.now(timezone.utc).isoformat()
    await db.study_plans.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"], "exam_date": body.exam_date,
            "target_score": body.target_score, "daily_hours": body.daily_hours,
            "class_level": body.class_level, "subjects": body.subjects,
            "plan": plan_data, "updated_at": now,
        }},
        upsert=True,
    )
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"exam_date": body.exam_date, "target_score": body.target_score}},
    )
    return {"plan": plan_data, "days_until_exam": days_until, "exam_date": body.exam_date}


@router.get("/study-plan")
async def get_study_plan(request: Request):
    user = await get_current_user(request)
    plan = await db.study_plans.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not plan:
        return {"plan": None}
    if plan.get("exam_date"):
        try:
            exam_dt = datetime.fromisoformat(plan["exam_date"].replace("Z", "+00:00"))
            plan["days_remaining"] = max(0, (exam_dt.replace(tzinfo=None) - datetime.now()).days)
        except Exception:
            pass
    return plan
