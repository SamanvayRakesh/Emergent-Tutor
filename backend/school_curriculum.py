"""School-specific curriculum data.

Each school entry maps grade → subject → list of chapter dicts
matching the standard chapter format used throughout the app.

PDF URLs are from NCERT 2024-25 official textbooks:
  Science      → Curiosity         (hecu1): all 13 chapters
  Social Studies → Exploring Society (hees1): all 7 chapters
  Mathematics  → Ganita Prakash Part 1 (hegp1): 7 chapters
               → Ganita Prakash Part 2 (hegp2): 6 chapters (02-07)
  English      → Poorvi            (hepr1): 5 chapters (01-05)
"""

NCERT = "https://ncert.nic.in/textbook/pdf/"

# ── Brooklyn National Public School — Grade 8 ────────────────────────────────

_BNPS_8_SCIENCE = [
    {"id": "bnps-8-sci-1",  "name": "Exploring the Investigative World of Science",         "order": 1,  "chapter_no": 1,  "pdf_url": f"{NCERT}hecu101.pdf"},
    {"id": "bnps-8-sci-2",  "name": "The Invisible Living World: Beyond Our Naked Eye",      "order": 2,  "chapter_no": 2,  "pdf_url": f"{NCERT}hecu102.pdf"},
    {"id": "bnps-8-sci-3",  "name": "Health: The Ultimate Treasure",                         "order": 3,  "chapter_no": 3,  "pdf_url": f"{NCERT}hecu103.pdf"},
    {"id": "bnps-8-sci-4",  "name": "Electricity: Magnetic and Heating Effects",             "order": 4,  "chapter_no": 4,  "pdf_url": f"{NCERT}hecu104.pdf"},
    {"id": "bnps-8-sci-5",  "name": "Exploring Forces",                                      "order": 5,  "chapter_no": 5,  "pdf_url": f"{NCERT}hecu105.pdf"},
    {"id": "bnps-8-sci-6",  "name": "Pressure, Winds, Storms, and Cyclones",                 "order": 6,  "chapter_no": 6,  "pdf_url": f"{NCERT}hecu106.pdf"},
    {"id": "bnps-8-sci-7",  "name": "Particulate Nature of Matter",                          "order": 7,  "chapter_no": 7,  "pdf_url": f"{NCERT}hecu107.pdf"},
    {"id": "bnps-8-sci-8",  "name": "Nature of Matter: Elements, Compounds, and Mixtures",  "order": 8,  "chapter_no": 8,  "pdf_url": f"{NCERT}hecu108.pdf"},
    {"id": "bnps-8-sci-9",  "name": "The Amazing World of Solutes, Solvents and Solutions",  "order": 9,  "chapter_no": 9,  "pdf_url": f"{NCERT}hecu109.pdf"},
    {"id": "bnps-8-sci-10", "name": "Light: Mirrors and Lenses",                             "order": 10, "chapter_no": 10, "pdf_url": f"{NCERT}hecu110.pdf"},
    {"id": "bnps-8-sci-11", "name": "Keeping Time with the Skies",                           "order": 11, "chapter_no": 11, "pdf_url": f"{NCERT}hecu111.pdf"},
    {"id": "bnps-8-sci-12", "name": "How Nature Works in Harmony",                           "order": 12, "chapter_no": 12, "pdf_url": f"{NCERT}hecu112.pdf"},
    {"id": "bnps-8-sci-13", "name": "Our Home: Earth, a Unique Life Sustaining Planet",      "order": 13, "chapter_no": 13, "pdf_url": f"{NCERT}hecu113.pdf"},
]

_BNPS_8_MATHS = [
    # hegp1 Part 1 (chapters 01-07 confirmed)
    {"id": "bnps-8-mth-1",  "name": "Rational Numbers",                            "order": 1,  "chapter_no": 1,  "pdf_url": f"{NCERT}hegp101.pdf"},
    {"id": "bnps-8-mth-2",  "name": "Exponents and Powers",                        "order": 2,  "chapter_no": 2,  "pdf_url": f"{NCERT}hegp202.pdf"},
    {"id": "bnps-8-mth-3",  "name": "Squares and Square Roots",                    "order": 3,  "chapter_no": 3,  "pdf_url": f"{NCERT}hegp106.pdf"},
    {"id": "bnps-8-mth-4",  "name": "Cubes and Cube Roots",                        "order": 4,  "chapter_no": 4,  "pdf_url": f"{NCERT}hegp107.pdf"},
    {"id": "bnps-8-mth-5",  "name": "Playing with Numbers",                        "order": 5,  "chapter_no": 5,  "pdf_url": f"{NCERT}hegp203.pdf"},
    {"id": "bnps-8-mth-6",  "name": "Algebraic Expressions and Identities",        "order": 6,  "chapter_no": 6,  "pdf_url": f"{NCERT}hegp204.pdf"},
    {"id": "bnps-8-mth-7",  "name": "Factorisation",                               "order": 7,  "chapter_no": 7,  "pdf_url": f"{NCERT}hegp205.pdf"},
    {"id": "bnps-8-mth-8",  "name": "Linear Equations in One Variable",            "order": 8,  "chapter_no": 8,  "pdf_url": f"{NCERT}hegp102.pdf"},
    {"id": "bnps-8-mth-9",  "name": "Comparing Quantities",                        "order": 9,  "chapter_no": 9,  "pdf_url": f"{NCERT}hegp206.pdf"},
    {"id": "bnps-8-mth-10", "name": "Direct and Indirect Variations",              "order": 10, "chapter_no": 10, "pdf_url": f"{NCERT}hegp207.pdf"},
    {"id": "bnps-8-mth-11", "name": "Understanding Quadrilaterals",                "order": 11, "chapter_no": 11, "pdf_url": f"{NCERT}hegp103.pdf"},
    {"id": "bnps-8-mth-12", "name": "Visualising Solid Shapes",                    "order": 12, "chapter_no": 12, "pdf_url": None},
    {"id": "bnps-8-mth-13", "name": "Practical Geometry",                          "order": 13, "chapter_no": 13, "pdf_url": f"{NCERT}hegp104.pdf"},
    {"id": "bnps-8-mth-14", "name": "Mensuration",                                 "order": 14, "chapter_no": 14, "pdf_url": None},
    {"id": "bnps-8-mth-15", "name": "Introduction to Graphs",                      "order": 15, "chapter_no": 15, "pdf_url": None},
    {"id": "bnps-8-mth-16", "name": "Data Handling",                               "order": 16, "chapter_no": 16, "pdf_url": f"{NCERT}hegp105.pdf"},
]

_BNPS_8_SST = [
    {"id": "bnps-8-sst-1", "name": "Natural Resources: Treasures of The Earth",               "order": 1, "chapter_no": 1, "pdf_url": f"{NCERT}hees101.pdf"},
    {"id": "bnps-8-sst-2", "name": "The Changing Political Landscape of India",                "order": 2, "chapter_no": 2, "pdf_url": f"{NCERT}hees102.pdf"},
    {"id": "bnps-8-sst-3", "name": "The Rise of the Marathas",                                 "order": 3, "chapter_no": 3, "pdf_url": f"{NCERT}hees103.pdf"},
    {"id": "bnps-8-sst-4", "name": "The Colonial Transformation of India",                     "order": 4, "chapter_no": 4, "pdf_url": f"{NCERT}hees104.pdf"},
    {"id": "bnps-8-sst-5", "name": "From Ballot to Bharat: The Spirit of Universal Franchise", "order": 5, "chapter_no": 5, "pdf_url": f"{NCERT}hees105.pdf"},
    {"id": "bnps-8-sst-6", "name": "The Parliamentary System: Legislature and Executive",      "order": 6, "chapter_no": 6, "pdf_url": f"{NCERT}hees106.pdf"},
    {"id": "bnps-8-sst-7", "name": "Resources at Work",                                        "order": 7, "chapter_no": 7, "pdf_url": f"{NCERT}hees107.pdf"},
]

_BNPS_8_ENG = [
    {"id": "bnps-8-eng-1",  "name": "The Time Machine",                    "order": 1,  "chapter_no": 1,  "type": "Story",        "author": "H.G. Wells",                  "pdf_url": f"{NCERT}hepr101.pdf"},
    {"id": "bnps-8-eng-2",  "name": "When the Mop Count Did Not Tally",    "order": 2,  "chapter_no": 2,  "type": "Story",        "author": "Sudha Murty",                 "pdf_url": f"{NCERT}hepr102.pdf"},
    {"id": "bnps-8-eng-3",  "name": "Stopping by Woods on a Snowy Evening","order": 3,  "chapter_no": 3,  "type": "Poem",         "author": "Robert Frost",                "pdf_url": f"{NCERT}hepr103.pdf"},
    {"id": "bnps-8-eng-4",  "name": "The Portrait of a Lady",              "order": 4,  "chapter_no": 4,  "type": "Story",        "author": "Khushwant Singh",             "pdf_url": f"{NCERT}hepr104.pdf"},
    {"id": "bnps-8-eng-5",  "name": "Stuart Little",                       "order": 5,  "chapter_no": 5,  "type": "Graphic Story","author": "E.B. White",                  "pdf_url": f"{NCERT}hepr105.pdf"},
    {"id": "bnps-8-eng-6",  "name": "Robots in Everyday Life",             "order": 6,  "chapter_no": 6,  "type": "Project",                                               "pdf_url": None},
    {"id": "bnps-8-eng-7",  "name": "Knowing Your Strengths",              "order": 7,  "chapter_no": 7,  "type": "Life Skills",                                           "pdf_url": None},
    {"id": "bnps-8-eng-8",  "name": "The Children's Hour",                 "order": 8,  "chapter_no": 8,  "type": "Poem",         "author": "Henry Wadsworth Longfellow",  "pdf_url": None},
    {"id": "bnps-8-eng-9",  "name": "That Little Square Box",              "order": 9,  "chapter_no": 9,  "type": "Story",        "author": "Sir Arthur Conan Doyle",      "pdf_url": None},
    {"id": "bnps-8-eng-10", "name": "Haunted",                             "order": 10, "chapter_no": 10, "type": "Story",        "author": "Harris Tobias",               "pdf_url": None},
    {"id": "bnps-8-eng-11", "name": "On the Grasshopper and Cricket",      "order": 11, "chapter_no": 11, "type": "Poem",         "author": "John Keats",                  "pdf_url": None},
    {"id": "bnps-8-eng-12", "name": "The Canterville Ghost",               "order": 12, "chapter_no": 12, "type": "Play",         "author": "Oscar Wilde",                 "pdf_url": None},
    {"id": "bnps-8-eng-13", "name": "Night of the Scorpion",               "order": 13, "chapter_no": 13, "type": "Poem",         "author": "Nissim Ezekiel",              "pdf_url": None},
]

# ── School registry ───────────────────────────────────────────────────────────

SCHOOLS: dict = {
    "brooklyn_national": {
        "id":         "brooklyn_national",
        "name":       "Brooklyn National Public School",
        "short_name": "Brooklyn National",
        "available_grades": ["8"],
        "curriculum": {
            "8": {
                "Science":       _BNPS_8_SCIENCE,
                "Mathematics":   _BNPS_8_MATHS,
                "Social Studies": _BNPS_8_SST,
                "English":       _BNPS_8_ENG,
            }
        },
    }
}

# List of all schools for the signup UI (includes "coming soon" entries)
SCHOOL_LIST = [
    {"id": "brooklyn_national", "name": "Brooklyn National Public School", "available": True},
    {"id": "national_public",   "name": "National Public School",          "available": False, "note": "Coming Soon"},
]

# ── Helper functions ──────────────────────────────────────────────────────────

def has_school_curriculum(school_id: str, grade: str) -> bool:
    s = SCHOOLS.get(school_id)
    return bool(s and grade in s.get("curriculum", {}))


def get_school_subjects(school_id: str, grade: str) -> list[dict]:
    """Return subject metadata list for a school+grade, or [] if not available."""
    s = SCHOOLS.get(school_id)
    if not s:
        return []
    grades = s.get("curriculum", {})
    subjects = grades.get(grade, {})
    _ICON_MAP = {
        "Mathematics":    ("Calculator", "#22d3ee"),
        "Science":        ("Atom",       "#8b5cf6"),
        "English":        ("Book",       "#f59e0b"),
        "Social Studies": ("Globe",      "#3b82f6"),
    }
    result = []
    for subj, chapters in subjects.items():
        icon, color = _ICON_MAP.get(subj, ("BookOpen", "#94a3b8"))
        result.append({
            "name": subj, "icon": icon, "color": color,
            "chapter_count": len(chapters), "verified": True,
        })
    return result


def get_school_chapters(school_id: str, grade: str, subject: str) -> list[dict]:
    """Return chapters for a school+grade+subject, or [] if not available."""
    s = SCHOOLS.get(school_id)
    if not s:
        return []
    base = s.get("curriculum", {}).get(grade, {}).get(subject, [])
    # Enrich with consistent fields
    return [
        {**c, "verified": True, "book_title": subject,
         "_meta": {"school": s["name"], "grade": grade, "subject": subject}}
        for c in base
    ]


def get_chapter_context_hint(school_id: str, grade: str, subject: str, chapter: str) -> str:
    """Return a short context hint for the AI tutor about a school-specific chapter."""
    if subject == "English":
        # Find the chapter and include author/type info
        chapters = get_school_chapters(school_id, grade, subject)
        for c in chapters:
            if c["name"].lower() == chapter.lower():
                ctype = c.get("type", "literary piece")
                author = c.get("author", "")
                author_str = f" by {author}" if author else ""
                return (
                    f'This is a Grade {grade} English {ctype.lower()}{author_str} '
                    f'titled "{chapter}". '
                    f'Teach literary analysis, themes, characters, narrative structure, '
                    f'vocabulary, and comprehension questions appropriate for Grade {grade} students.'
                )
    return ""
