"""NIOS Secondary Course curriculum data (Class 10 equivalent).

Subjects covered: those with PDFs in /app/nios_syllabus/.
Chapters extracted from PDF structure + official NIOS curriculum.
"""

# ── NIOS Secondary Subjects ───────────────────────────────────────────────────

_NIOS_ACCOUNTANCY = [
    {"id": "nios-acc-1",  "name": "Introduction to Accounting",                "order": 1,  "chapter_no": 1},
    {"id": "nios-acc-2",  "name": "Accounting Concepts and Conventions",        "order": 2,  "chapter_no": 2},
    {"id": "nios-acc-3",  "name": "Accounting Equation",                        "order": 3,  "chapter_no": 3},
    {"id": "nios-acc-4",  "name": "Recording of Transactions - Journal",        "order": 4,  "chapter_no": 4},
    {"id": "nios-acc-5",  "name": "Ledger",                                     "order": 5,  "chapter_no": 5},
    {"id": "nios-acc-6",  "name": "Cash Book",                                  "order": 6,  "chapter_no": 6},
    {"id": "nios-acc-7",  "name": "Trial Balance",                              "order": 7,  "chapter_no": 7},
    {"id": "nios-acc-8",  "name": "Financial Statements",                       "order": 8,  "chapter_no": 8},
]

_NIOS_BUSINESS_STUDIES = [
    {"id": "nios-bst-1",  "name": "Nature and Scope of Business",               "order": 1,  "chapter_no": 1},
    {"id": "nios-bst-2",  "name": "Industry and Commerce",                      "order": 2,  "chapter_no": 2},
    {"id": "nios-bst-3",  "name": "Forms of Business Organisation - I",         "order": 3,  "chapter_no": 3},
    {"id": "nios-bst-4",  "name": "Forms of Business Organisation - II",        "order": 4,  "chapter_no": 4},
    {"id": "nios-bst-5",  "name": "Public Sector Enterprises",                  "order": 5,  "chapter_no": 5},
    {"id": "nios-bst-6",  "name": "Insurance",                                  "order": 6,  "chapter_no": 6},
    {"id": "nios-bst-7",  "name": "Transport",                                  "order": 7,  "chapter_no": 7},
    {"id": "nios-bst-8",  "name": "Communication",                              "order": 8,  "chapter_no": 8},
    {"id": "nios-bst-9",  "name": "Warehousing",                                "order": 9,  "chapter_no": 9},
    {"id": "nios-bst-10", "name": "Trade",                                      "order": 10, "chapter_no": 10},
    {"id": "nios-bst-11", "name": "Advertising",                                "order": 11, "chapter_no": 11},
    {"id": "nios-bst-12", "name": "Import Trade Procedures",                    "order": 12, "chapter_no": 12},
    {"id": "nios-bst-13", "name": "Government and Business",                    "order": 13, "chapter_no": 13},
    {"id": "nios-bst-14", "name": "Consumer Protection",                        "order": 14, "chapter_no": 14},
    {"id": "nios-bst-15", "name": "Business Finance",                           "order": 15, "chapter_no": 15},
]

_NIOS_DATA_ENTRY = [
    {"id": "nios-deo-1",  "name": "Computer Fundamentals",                      "order": 1,  "chapter_no": 1},
    {"id": "nios-deo-2",  "name": "Input and Output Devices",                   "order": 2,  "chapter_no": 2},
    {"id": "nios-deo-3",  "name": "Storage Devices",                            "order": 3,  "chapter_no": 3},
    {"id": "nios-deo-4",  "name": "Operating System",                           "order": 4,  "chapter_no": 4},
    {"id": "nios-deo-5",  "name": "Word Processing",                            "order": 5,  "chapter_no": 5},
    {"id": "nios-deo-6",  "name": "Spreadsheets",                               "order": 6,  "chapter_no": 6},
    {"id": "nios-deo-7",  "name": "Computer Networks and Internet",              "order": 7,  "chapter_no": 7},
    {"id": "nios-deo-8",  "name": "Data Entry and Keyboarding Skills",           "order": 8,  "chapter_no": 8},
]

_NIOS_ECONOMICS = [
    {"id": "nios-eco-1",  "name": "Meaning and Nature of Economics",            "order": 1,  "chapter_no": 1},
    {"id": "nios-eco-2",  "name": "Basic Concepts of Economics",                "order": 2,  "chapter_no": 2},
    {"id": "nios-eco-3",  "name": "Consumer Behaviour",                         "order": 3,  "chapter_no": 3},
    {"id": "nios-eco-4",  "name": "Theory of Demand",                           "order": 4,  "chapter_no": 4},
    {"id": "nios-eco-5",  "name": "Theory of Supply",                           "order": 5,  "chapter_no": 5},
    {"id": "nios-eco-6",  "name": "Market Equilibrium",                         "order": 6,  "chapter_no": 6},
    {"id": "nios-eco-7",  "name": "Theory of Production",                       "order": 7,  "chapter_no": 7},
    {"id": "nios-eco-8",  "name": "Theory of Cost",                             "order": 8,  "chapter_no": 8},
    {"id": "nios-eco-9",  "name": "National Income",                            "order": 9,  "chapter_no": 9},
    {"id": "nios-eco-10", "name": "Money and Banking",                          "order": 10, "chapter_no": 10},
    {"id": "nios-eco-11", "name": "Government Budget",                          "order": 11, "chapter_no": 11},
    {"id": "nios-eco-12", "name": "India's Foreign Trade",                      "order": 12, "chapter_no": 12},
]

_NIOS_ENGLISH = [
    {"id": "nios-eng-1",  "name": "Snake Bite",                                 "order": 1,  "chapter_no": 1},
    {"id": "nios-eng-2",  "name": "How the Squirrel Got His Stripes",           "order": 2,  "chapter_no": 2},
    {"id": "nios-eng-3",  "name": "Kondiba - A Hero",                           "order": 3,  "chapter_no": 3},
    {"id": "nios-eng-4",  "name": "Tall Trees",                                 "order": 4,  "chapter_no": 4},
    {"id": "nios-eng-5",  "name": "A Tiger Comes to Town - I",                  "order": 5,  "chapter_no": 5},
    {"id": "nios-eng-6",  "name": "A Tiger Comes to Town - II",                 "order": 6,  "chapter_no": 6},
    {"id": "nios-eng-7",  "name": "The Shoeshine",                              "order": 7,  "chapter_no": 7},
    {"id": "nios-eng-8",  "name": "A Birthday Letter",                          "order": 8,  "chapter_no": 8},
    {"id": "nios-eng-9",  "name": "Nine Gold Medals",                           "order": 9,  "chapter_no": 9},
    {"id": "nios-eng-10", "name": "Noise: How It Affects Our Lives",            "order": 10, "chapter_no": 10},
    {"id": "nios-eng-11", "name": "My Elder Brother",                           "order": 11, "chapter_no": 11},
    {"id": "nios-eng-12", "name": "Indian Weavers",                             "order": 12, "chapter_no": 12},
    {"id": "nios-eng-13", "name": "The Last Stone Mason",                       "order": 13, "chapter_no": 13},
    {"id": "nios-eng-14", "name": "Stealing and Atonement",                     "order": 14, "chapter_no": 14},
    {"id": "nios-eng-15", "name": "My Vision for India",                        "order": 15, "chapter_no": 15},
    {"id": "nios-eng-16", "name": "My Only Cry",                                "order": 16, "chapter_no": 16},
    {"id": "nios-eng-17", "name": "Caring for Others",                          "order": 17, "chapter_no": 17},
    {"id": "nios-eng-18", "name": "The Little Girl",                            "order": 18, "chapter_no": 18},
    {"id": "nios-eng-19", "name": "A Prayer for Healing",                       "order": 19, "chapter_no": 19},
    {"id": "nios-eng-20", "name": "New Good Things from Rubbish",               "order": 20, "chapter_no": 20},
    {"id": "nios-eng-21", "name": "The Village Schoolmaster",                   "order": 21, "chapter_no": 21},
    {"id": "nios-eng-22", "name": "The Truth",                                  "order": 22, "chapter_no": 22},
    {"id": "nios-eng-23", "name": "The Return of the Lion",                     "order": 23, "chapter_no": 23},
    {"id": "nios-eng-24", "name": "Co-operate",                                 "order": 24, "chapter_no": 24},
    {"id": "nios-eng-25", "name": "Once Upon a Time",                           "order": 25, "chapter_no": 25},
    {"id": "nios-eng-26", "name": "Ustad",                                      "order": 26, "chapter_no": 26},
    {"id": "nios-eng-27", "name": "The Parrot Who Wouldn't Talk",               "order": 27, "chapter_no": 27},
]

_NIOS_ENTREPRENEURSHIP = [
    {"id": "nios-ent-1",  "name": "Introduction to Entrepreneurship",           "order": 1,  "chapter_no": 1},
    {"id": "nios-ent-2",  "name": "Self-Employment",                            "order": 2,  "chapter_no": 2},
    {"id": "nios-ent-3",  "name": "Identifying Business Opportunities",          "order": 3,  "chapter_no": 3},
    {"id": "nios-ent-4",  "name": "Starting a Small Business",                  "order": 4,  "chapter_no": 4},
    {"id": "nios-ent-5",  "name": "Business Plan",                              "order": 5,  "chapter_no": 5},
    {"id": "nios-ent-6",  "name": "Resource Mobilisation",                      "order": 6,  "chapter_no": 6},
    {"id": "nios-ent-7",  "name": "Legal Aspects of Business",                  "order": 7,  "chapter_no": 7},
]

_NIOS_FOLK_ART = [
    {"id": "nios-fart-1", "name": "Introduction to Folk and Tribal Art",        "order": 1,  "chapter_no": 1},
    {"id": "nios-fart-2", "name": "Forms of Folk and Tribal Art",               "order": 2,  "chapter_no": 2},
    {"id": "nios-fart-3", "name": "Contribution of Scholars and Artists",       "order": 3,  "chapter_no": 3},
    {"id": "nios-fart-4", "name": "Traditional and Contemporary Methods",       "order": 4,  "chapter_no": 4},
    {"id": "nios-fart-5", "name": "Symbols and Motifs of Folk Art",             "order": 5,  "chapter_no": 5},
]

# ── Subject metadata (icon + color for UI) ────────────────────────────────────

_NIOS_SUBJECT_META = {
    "Accountancy":            ("TrendingUp", "#10b981"),
    "Business Studies":       ("Briefcase",  "#3b82f6"),
    "Data Entry Operations":  ("Monitor",    "#6366f1"),
    "Economics":              ("BarChart2",  "#f59e0b"),
    "English":                ("BookOpen",   "#ec4899"),
    "Entrepreneurship":       ("Zap",        "#8b5cf6"),
    "Folk Art":               ("Palette",    "#f97316"),
}

# ── Subject → chapters mapping ────────────────────────────────────────────────

NIOS_CURRICULUM: dict = {
    "Accountancy":           _NIOS_ACCOUNTANCY,
    "Business Studies":      _NIOS_BUSINESS_STUDIES,
    "Data Entry Operations": _NIOS_DATA_ENTRY,
    "Economics":             _NIOS_ECONOMICS,
    "English":               _NIOS_ENGLISH,
    "Entrepreneurship":      _NIOS_ENTREPRENEURSHIP,
    "Folk Art":              _NIOS_FOLK_ART,
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_nios_subjects() -> list[dict]:
    result = []
    for subj, chapters in NIOS_CURRICULUM.items():
        icon, color = _NIOS_SUBJECT_META.get(subj, ("BookOpen", "#94a3b8"))
        result.append({
            "name": subj, "icon": icon, "color": color,
            "chapter_count": len(chapters), "verified": True,
        })
    return result


def get_nios_chapters(subject: str) -> list[dict]:
    chapters = NIOS_CURRICULUM.get(subject, [])
    return [
        {**c, "verified": True, "book_title": f"NIOS Secondary - {subject}",
         "_meta": {"curriculum": "NIOS Secondary", "grade": "10", "subject": subject}}
        for c in chapters
    ]
