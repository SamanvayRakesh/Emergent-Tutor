"""Quiz generation + submission + gamification stats."""
import uuid
import json
import re
import random
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core import db, openai_client, get_current_user
from plan_gates import check_limit, increment_usage
from models import QuizGenerateRequest, QuizSubmitRequest
from adaptive_engine import record_quiz_result, update_topic_performance, get_student_profile
from school_curriculum import get_school_chapters, has_school_curriculum

router = APIRouter()

# ── CBSE chapter subtopics mapping ────────────────────────────────────────────
# Format: { "chapter name (lowercase)": ["Subtopic 1", ...] }
_SUBTOPICS: dict = {
    # Class 10 Maths
    "real numbers": ["Euclid's Division Lemma", "Fundamental Theorem of Arithmetic", "Irrational Numbers", "Rational Numbers & Decimals"],
    "polynomials": ["Zeros of Polynomials", "Relationship between Zeros & Coefficients", "Division Algorithm"],
    "pair of linear equations in two variables": ["Graphical Method", "Substitution Method", "Elimination Method", "Cross Multiplication"],
    "quadratic equations": ["Factorisation Method", "Completing the Square", "Quadratic Formula", "Nature of Roots"],
    "arithmetic progressions": ["nth Term of AP", "Sum of First n Terms", "Applications of AP"],
    "triangles": ["Similarity of Triangles", "Basic Proportionality Theorem", "Pythagoras Theorem", "Areas of Similar Triangles"],
    "coordinate geometry": ["Distance Formula", "Section Formula", "Midpoint Formula", "Area of a Triangle"],
    "introduction to trigonometry": ["Trigonometric Ratios", "Trigonometric Identities", "Values of Specific Angles"],
    "some applications of trigonometry": ["Heights and Distances", "Angle of Elevation", "Angle of Depression"],
    "circles": ["Tangent to a Circle", "Number of Tangents from a Point", "Properties of Tangents"],
    "areas related to circles": ["Perimeter and Area of a Circle", "Areas of Sector and Segment", "Combination Figures"],
    "surface areas and volumes": ["Surface Area of Cuboid & Cylinder", "Volume of Cone & Sphere", "Conversion of Solids", "Frustum of a Cone"],
    "statistics": ["Mean", "Median", "Mode", "Cumulative Frequency"],
    "probability": ["Classical Probability", "Complementary Events", "Problems on Playing Cards & Dice"],
    # Class 10 Science
    "chemical reactions and equations": ["Types of Chemical Reactions", "Balancing Equations", "Oxidation & Reduction"],
    "acids, bases and salts": ["Properties of Acids & Bases", "pH Scale", "Salts & Their Properties"],
    "metals and non-metals": ["Physical Properties", "Chemical Properties", "Reactivity Series", "Ionic Compounds"],
    "carbon and its compounds": ["Bonding in Carbon", "Homologous Series", "Functional Groups", "Chemical Properties"],
    "life processes": ["Nutrition", "Respiration", "Transportation", "Excretion"],
    "control and coordination": ["Nervous System", "Hormones", "Reflex Action", "Endocrine System"],
    "heredity and evolution": ["Mendel's Laws", "Sex Determination", "Evolution & Natural Selection"],
    "light - reflection and refraction": ["Laws of Reflection", "Spherical Mirrors", "Refraction of Light", "Lenses"],
    "electricity": ["Ohm's Law", "Resistance & Resistors", "Electric Power", "Heating Effect"],
    "magnetic effects of electric current": ["Magnetic Field", "Electromagnet", "Electric Motor", "Electromagnetic Induction"],
    # Class 9 Maths
    "number systems": ["Irrational Numbers", "Real Numbers on Number Line", "Laws of Exponents", "Decimal Expansions"],
    "linear equations in two variables": ["Graphical Representation", "Equations of Lines Parallel to Axes"],
    "euclid's geometry": ["Euclid's Axioms & Postulates", "Theorems based on Lines & Angles"],
    "lines and angles": ["Basic Terms", "Parallel Lines & Transversal", "Angle Sum Property"],
    "statistics": ["Collection of Data", "Graphical Representation", "Measures of Central Tendency"],
    # Class 9 Science
    "matter in our surroundings": ["States of Matter", "Change of State", "Evaporation"],
    "is matter around us pure": ["Mixtures & Solutions", "Separation Techniques", "Elements & Compounds"],
    "atoms and molecules": ["Laws of Chemical Combination", "Atomic Mass", "Molecular Mass & Mole Concept"],
    "structure of atom": ["Thomson's Model", "Rutherford's Model", "Bohr's Model", "Valency & Electronic Configuration"],
    "motion": ["Distance & Displacement", "Speed & Velocity", "Acceleration", "Equations of Motion", "Graphical Representation"],
    "force and laws of motion": ["Newton's First Law", "Newton's Second Law", "Newton's Third Law", "Conservation of Momentum"],
    "gravitation": ["Universal Law of Gravitation", "Free Fall & Acceleration due to Gravity", "Thrust & Pressure", "Archimedes' Principle"],
    "work and energy": ["Work Done", "Kinetic & Potential Energy", "Power", "Law of Conservation of Energy"],
    # Class 8 BNPS / NCERT Mathematics (Ganita Prakash)
    "rational numbers": ["Properties of Rational Numbers", "Representation on Number Line", "Operations on Rational Numbers", "Rational Numbers between Two Rationals"],
    "exponents and powers": ["Laws of Exponents", "Negative Exponents", "Numbers in Standard Form", "Comparing Very Large & Small Numbers"],
    "squares and square roots": ["Perfect Squares & Patterns", "Finding Square Root by Division", "Square Root by Estimation", "Pythagorean Triplets"],
    "cubes and cube roots": ["Perfect Cubes", "Cube Root by Prime Factorisation", "Cube Root of Decimals"],
    "playing with numbers": ["Generalised Form of Numbers", "Games with Numbers", "Letters for Digits", "Divisibility Tests"],
    "algebraic expressions and identities": ["Terms & Factors", "Addition & Subtraction of Expressions", "Multiplication of Expressions", "Standard Identities"],
    "factorisation": ["Common Factors", "Factorising by Regrouping", "Factorisation using Identities", "Division of Algebraic Expressions"],
    "linear equations in one variable": ["Solving Linear Equations", "Applications: Word Problems", "Equations with Variables on Both Sides", "Reducing Equations to Simpler Form"],
    "comparing quantities": ["Ratios & Percentages", "Profit & Loss", "Simple Interest", "Compound Interest"],
    "direct and indirect variations": ["Direct Proportion", "Inverse Proportion", "Applications of Variation"],
    "understanding quadrilaterals": ["Angle Sum Property", "Types of Quadrilaterals", "Properties of Parallelogram", "Special Parallelograms"],
    "visualising solid shapes": ["Views of 3D Shapes", "Mapping Spaces", "Faces Edges & Vertices", "Euler's Formula"],
    "practical geometry": ["Constructing Quadrilaterals", "Special Quadrilaterals Construction", "Some Special Cases"],
    "mensuration": ["Area of Trapezium & General Quadrilateral", "Area of Polygons", "Surface Area of Cube & Cuboid", "Volume of Cube & Cuboid"],
    "introduction to graphs": ["Linear Graphs", "Types of Graphs", "Reading Graphs", "Drawing Graphs"],
    "data handling": ["Organising Data", "Grouping Data & Histograms", "Circle Graphs/Pie Charts", "Probability"],
    # Class 8 BNPS Science (Curiosity)
    "exploring the investigative world of science": ["Scientific Method", "Types of Investigations", "Making Observations", "Fair Testing"],
    "the invisible living world: beyond our naked eye": ["Microorganisms & Their Types", "Bacteria & Viruses", "Useful Microorganisms", "Harmful Microorganisms & Diseases"],
    "health: the ultimate treasure": ["Diseases & Their Causes", "Balanced Diet & Nutrition", "Healthcare & Hygiene", "Communicable vs Non-Communicable Diseases"],
    "electricity: magnetic and heating effects": ["Magnetic Effect of Current", "Electromagnets", "Electric Bell", "Heating Effect & Its Applications"],
    "exploring forces": ["Types of Forces", "Contact & Non-Contact Forces", "Effects of Force", "Friction & Its Applications"],
    "pressure, winds, storms, and cyclones": ["Air Pressure", "Atmospheric Pressure", "Wind & Weather", "Thunderstorms & Cyclones"],
    "particulate nature of matter": ["States of Matter", "Diffusion & Brownian Motion", "Kinetic Theory", "Change of State"],
    "nature of matter: elements, compounds, and mixtures": ["Elements & Symbols", "Compounds vs Mixtures", "Separation Techniques", "Physical & Chemical Changes"],
    "the amazing world of solutes, solvents and solutions": ["Types of Solutions", "Solubility & Factors", "Concentration of Solutions", "Saturated & Unsaturated Solutions"],
    "light: mirrors and lenses": ["Reflection & Laws", "Spherical Mirrors", "Refraction & Laws", "Lenses & Their Uses"],
    "keeping time with the skies": ["Solar & Lunar Calendar", "Phases of Moon", "Seasons", "Tides"],
    "how nature works in harmony": ["Food Chains & Webs", "Ecosystems", "Biodiversity", "Conservation"],
    "our home: earth, a unique life sustaining planet": ["Earth's Atmosphere", "Water Cycle", "Climate Change", "Sustainability"],
    # Class 8 BNPS Social Studies (Exploring Society)
    "natural resources: treasures of the earth": ["Types of Resources", "Land & Soil Resources", "Water Resources", "Mineral & Energy Resources"],
    "the changing political landscape of india": ["Mughal Empire Decline", "Rise of Regional Powers", "Maratha Confederacy", "European Powers in India"],
    "the rise of the marathas": ["Shivaji & Maratha Empire", "Administration", "Maratha Expansion", "Anglo-Maratha Wars"],
    "the colonial transformation of india": ["British East India Company", "Economic Exploitation", "Social & Cultural Impact", "Resistance Movements"],
    "from ballot to bharat: the spirit of universal franchise": ["Indian Constitution", "Universal Adult Franchise", "Elections in India", "Role of Election Commission"],
    "the parliamentary system: legislature and executive": ["Parliament Structure", "Lok Sabha & Rajya Sabha", "Role of President", "Prime Minister & Council of Ministers"],
    "resources at work": ["Human Resources", "Agricultural Resources", "Industrial Resources", "Sustainable Development"],
    # Class 8 BNPS English (Poorvi)
    "the time machine": ["Plot Summary", "Characters", "Science Fiction Elements", "Themes of Time & Society"],
    "when the mop count did not tally": ["Story Plot", "Characters", "Themes of Honesty & Integrity", "Narrative Style"],
    "stopping by woods on a snowy evening": ["Poem Analysis", "Literary Devices", "Themes & Symbolism", "Tone & Mood"],
    "the portrait of a lady": ["Character of Grandmother", "Themes of Old Age & Modernity", "Narrative Perspective", "Key Scenes"],
    "stuart little": ["Story Overview", "Stuart as a Character", "Adventures & Themes", "Graphic Story Elements"],
    "robots in everyday life": ["Types of Robots", "Applications of Robotics", "Impact on Society", "Future of Robots"],
    "knowing your strengths": ["Self-Awareness", "Identifying Strengths", "Building Confidence", "Life Skills Application"],
    "the children's hour": ["Poem Analysis", "Family & Childhood Themes", "Poetic Devices", "Longfellow's Style"],
    "that little square box": ["Plot & Mystery Elements", "Sherlock Holmes Style", "Characters & Clues", "Resolution"],
    "haunted": ["Ghost Story Elements", "Plot Analysis", "Atmosphere & Setting", "Character Reactions"],
    "on the grasshopper and cricket": ["Poem Analysis", "Nature Themes", "Keats' Romantic Style", "Poetic Devices"],
    "the canterville ghost": ["Play Summary", "Comedy & Gothic Elements", "Characters", "Oscar Wilde's Satire"],
    "night of the scorpion": ["Poem Analysis", "Themes of Superstition & Faith", "Cultural Context", "Ezekiel's Style"],
}

def _get_subtopics(chapter: str) -> list[str]:
    """Return subtopics for a chapter. Falls back to a generic split."""
    key = chapter.lower().strip()
    if key in _SUBTOPICS:
        return _SUBTOPICS[key]
    # Generic fallback — split chapter into concept buckets
    return [
        f"{chapter} — Introduction & Concepts",
        f"{chapter} — Key Definitions",
        f"{chapter} — Solved Examples",
        f"{chapter} — Practice Problems",
    ]


@router.get("/quiz/subtopics")
async def get_subtopics(class_level: str, subject: str, chapter: str, request: Request):
    """Return subtopics for a chapter to populate the quiz setup dropdown."""
    await get_current_user(request)
    return {"chapter": chapter, "subtopics": _get_subtopics(chapter)}

@router.post("/quiz/generate")
async def generate_quiz(body: QuizGenerateRequest, request: Request):
    user = await get_current_user(request)
    # Grade lock
    if body.class_level != user.get("class_level"):
        raise HTTPException(status_code=403, detail="Quizzes must match your active grade.")
    # Daily quiz limit
    allowed, info = await check_limit(user["user_id"], "quiz")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DAILY_LIMIT_REACHED", "feature": "quiz",
                "message": f"You've used all {info['limit']} quizzes on the Free plan today.",
                "limit_info": info, "upgrade_to": "pro",
            },
        )

    # Credit gate: first quiz is FREE; subsequent quizzes cost credits.
    # IMPORTANT: check balance first, deduct ONLY after successful generation
    # so users are NEVER charged for a failed or timed-out quiz.
    QUIZ_COST = 15
    past_quiz_count = await db.quizzes.count_documents({"user_id": user["user_id"]})
    if past_quiz_count > 0:
        if user.get("credits", 0) < QUIZ_COST:
            raise HTTPException(
                status_code=402,
                detail={"code": "INSUFFICIENT_CREDITS", "message": "Not enough credits to generate a quiz.", "required": QUIZ_COST, "current": user.get("credits", 0)},
            )

    # Build school context for BNPS students
    school = user.get("school", "")
    school_context = ""
    if school and has_school_curriculum(school, body.class_level):
        chapters = get_school_chapters(school, body.class_level, body.subject)
        ch_names = [c["name"] for c in chapters]
        school_context = (
            f"\nSCHOOL CONTEXT: This student attends Brooklyn National Public School (BNPS). "
            f"Generate questions strictly based on their syllabus for Grade {body.class_level} {body.subject}. "
            f"Syllabus chapters: {', '.join(ch_names)}. "
            f"Focus ONLY on the topic '{body.topic}' as it appears in the BNPS curriculum."
        )

    prompt = f"""Generate exactly {body.num_questions} multiple-choice questions for Grade {body.class_level} {body.subject} on topic: "{body.topic}".{school_context}
Difficulty: {body.difficulty}
Return ONLY valid JSON (no markdown, no extra text):
{{"title":"Quiz: {body.topic}","questions":[{{"type":"mcq","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"correct":"A","explanation":"One sentence."}}]}}"""

    # Scale token budget: ~130 tokens per question + 200 overhead (well within model capacity)
    max_tokens = min(body.num_questions * 130 + 250, 1400)

    try:
        response = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model="deepseek/deepseek-v4-flash",
                messages=[
                    {"role": "system", "content": "You are a CBSE quiz generator. Return ONLY valid JSON, no extra text."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                extra_body={"include_reasoning": False},
            ),
            timeout=50.0,   # hard cap — Cloudflare proxy limit is 120 s, stay well under it
        )
        raw = response.choices[0].message.content or ""
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            raise ValueError("Model returned no JSON object")
        quiz_data = json.loads(m.group())
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Quiz generation timed out. No credits were charged. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Quiz generation failed. No credits were charged. ({type(e).__name__})")

    # ── Only deduct credits AFTER the quiz is successfully generated ──────────
    if past_quiz_count > 0:
        await db.users.update_one({"user_id": user["user_id"]}, {"$inc": {"credits": -QUIZ_COST}})

    quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    # Normalize questions: ensure every question has type="mcq" as fallback
    raw_questions = quiz_data.get("questions", [])
    for q in raw_questions:
        if not q.get("type"):
            q["type"] = "mcq" if q.get("options") else "short_answer"

    quiz_doc = {
        "quiz_id": quiz_id, "user_id": user["user_id"],
        "class_level": body.class_level, "subject": body.subject,
        "topic": body.topic, "difficulty": body.difficulty,
        "questions": raw_questions,
        "title": quiz_data.get("title", f"Quiz: {body.topic}"),
        "completed": False, "score": None, "created_at": now,
    }
    await db.quizzes.insert_one(quiz_doc)
    await increment_usage(user["user_id"], "quizzes", 1)
    quiz_doc.pop("_id", None)
    return quiz_doc


@router.get("/quiz/history")
async def get_quiz_history(request: Request):
    user = await get_current_user(request)
    return await db.quizzes.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)


@router.get("/quiz/topic-mastery")
async def get_topic_mastery(topic: str, request: Request):
    """Return adaptive difficulty recommendation for a topic based on quiz history."""
    user = await get_current_user(request)
    profile = await db.student_profiles.find_one({"user_id": user["user_id"]}, {"_id": 0, "topics": 1})
    if not profile:
        return {"topic": topic, "mastery": 0.5, "recommended_difficulty": "medium", "attempts": 0}
    data = profile.get("topics", {}).get(topic, {})
    mastery = data.get("mastery", 0.5)
    attempts = data.get("attempts", 0)
    if mastery < 0.4:
        difficulty = "easy"
    elif mastery < 0.7:
        difficulty = "medium"
    else:
        difficulty = "hard"
    return {
        "topic": topic,
        "mastery": round(mastery, 2),
        "mastery_pct": int(mastery * 100),
        "recommended_difficulty": difficulty,
        "attempts": attempts,
    }


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, body: QuizSubmitRequest, request: Request):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"quiz_id": quiz_id, "user_id": user["user_id"]}, {"_id": 0})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # ── Layer 1: Replay block ─────────────────────────────────────────────────
    if quiz.get("completed"):
        raise HTTPException(status_code=400, detail="This quiz has already been submitted.")

    questions = quiz.get("questions", [])
    correct_count = 0
    results = []
    for i, q in enumerate(questions):
        ua = body.answers.get(str(i))
        is_correct = ua == q.get("correct")
        if is_correct:
            correct_count += 1
        results.append({
            "question": q["question"], "user_answer": ua,
            "correct_answer": q.get("correct"),
            "is_correct": is_correct, "explanation": q.get("explanation", ""),
        })

    total = len(questions)
    score_pct = int((correct_count / total * 100)) if total > 0 else 0

    # XP calculation
    difficulty = quiz.get("difficulty", "medium")
    xp_per_correct = {"easy": 10, "medium": 15, "hard": 22}.get(difficulty, 15)
    base_xp = correct_count * xp_per_correct

    perfect_bonus = 25 if correct_count == total and total > 0 else 0

    streak = max_streak = 0
    for r in results:
        if r.get("is_correct"):
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    streak_bonus = max_streak * 2

    improvement_bonus = 0
    topic_key = quiz.get("topic", "")
    if score_pct >= 70 and topic_key:
        profile = await get_student_profile(user["user_id"])
        topic_mastery = profile.get("topics", {}).get(topic_key, {}).get("mastery", 0.5)
        if topic_mastery < 0.5:
            improvement_bonus = 50

    total_xp = base_xp + perfect_bonus + streak_bonus + improvement_bonus

    # ── Layer 2: Speed gate — too fast = answer-copying, 0 XP ────────────────
    speed_floor = {"easy": 6, "medium": 9, "hard": 14}   # min seconds per question
    min_seconds = total * speed_floor.get(difficulty, 9)
    try:
        quiz_created = datetime.fromisoformat(quiz["created_at"].replace("Z", "+00:00"))
        time_spent = (datetime.now(timezone.utc) - quiz_created).total_seconds()
    except (ValueError, AttributeError, KeyError):
        time_spent = 9999
    if time_spent < min_seconds:
        total_xp = 0

    # ── Layer 3: Per-topic daily decay — stops spam farming ───────────────────
    if total_xp > 0 and topic_key:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        topic_today = await db.quizzes.count_documents({
            "user_id": user["user_id"], "topic": topic_key,
            "completed": True, "completed_at": {"$gte": today_start},
        })
        # 1st quiz on topic: 100%, 2nd: 50%, 3rd+: 20%
        decay = [1.0, 0.5, 0.2]
        multiplier = decay[min(topic_today, len(decay) - 1)]
        total_xp = int(total_xp * multiplier)

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.quizzes.update_one(
        {"quiz_id": quiz_id},
        {"$set": {"completed": True, "score": score_pct, "correct_count": correct_count,
                  "total_questions": total, "completed_at": now_iso}},
    )
    if total_xp > 0:
        await db.users.update_one(
            {"user_id": user["user_id"]}, {"$inc": {"xp": total_xp}}
        )
        updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "xp": 1, "level": 1})
        if updated:
            new_level = max(1, updated.get("xp", 0) // 500 + 1)
            if new_level > updated.get("level", 1):
                await db.users.update_one(
                    {"user_id": user["user_id"]}, {"$set": {"level": new_level}}
                )

    await record_quiz_result(user["user_id"], quiz.get("topic", "General"), score_pct, correct_count, total)
    for i, q in enumerate(questions):
        ua = body.answers.get(str(i))
        is_correct = ua == q.get("correct")
        topic_label = q.get("topic") or quiz.get("topic") or quiz.get("chapter") or "General"
        await update_topic_performance(user["user_id"], topic_label, is_correct)

    return {"score": score_pct, "correct_count": correct_count, "total_questions": total,
            "xp_earned": total_xp, "improvement_bonus": improvement_bonus,
            "perfect_bonus": perfect_bonus, "streak_bonus": streak_bonus,
            "results": results}
@router.get("/gamification/stats")
async def get_gamification_stats(request: Request):
    user = await get_current_user(request)
    xp = user.get("xp", 0)
    level = max(1, xp // 500 + 1)
    xp_in_level = xp % 500

    session_count = await db.chat_sessions.count_documents({"user_id": user["user_id"]})
    quiz_count = await db.quizzes.count_documents({"user_id": user["user_id"], "completed": True})
    chapters_studied = await db.progress.count_documents({"user_id": user["user_id"]})

    achievements = []
    if session_count >= 1:
        achievements.append({"id": "first_chat", "name": "First Steps", "description": "Started your first AI chat", "icon": "star", "color": "#22d3ee"})
    if session_count >= 10:
        achievements.append({"id": "chat_10", "name": "Curious Mind", "description": "Completed 10 AI chat sessions", "icon": "brain", "color": "#8b5cf6"})
    if quiz_count >= 1:
        achievements.append({"id": "first_quiz", "name": "Quiz Starter", "description": "Completed your first quiz", "icon": "target", "color": "#10b981"})
    if quiz_count >= 5:
        achievements.append({"id": "quiz_5", "name": "Quiz Master", "description": "Completed 5 quizzes", "icon": "trophy", "color": "#f59e0b"})
    if xp >= 100:
        achievements.append({"id": "xp_100", "name": "Rising Star", "description": "Earned 100 XP", "icon": "zap", "color": "#d946ef"})
    if user.get("streak", 0) >= 3:
        achievements.append({"id": "streak_3", "name": "On Fire!", "description": "3-day learning streak", "icon": "flame", "color": "#ef4444"})

    daily_topics = ["Photosynthesis", "Newton's Laws", "Quadratic Equations", "Periodic Table", "French Revolution", "Python Lists"]
    random.seed(datetime.now().date().toordinal())
    daily_topic = random.choice(daily_topics)

    return {
        "xp": xp, "level": level, "xp_in_level": xp_in_level, "xp_to_next": 500 - xp_in_level,
        "streak": user.get("streak", 0), "longest_streak": user.get("longest_streak", 0),
        "achievements": achievements,
        "session_count": session_count, "quiz_count": quiz_count, "chapters_studied": chapters_studied,
        "daily_challenge": {"topic": daily_topic, "subject": "Mixed", "xp_reward": 50},
    }
