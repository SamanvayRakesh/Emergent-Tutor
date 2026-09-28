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

_NIOS_HOME_SCIENCE = [
    {"id": "nios-hs-1",  "name": "Food, Nutrition and Health",                   "order": 1,  "chapter_no": 1},
    {"id": "nios-hs-2",  "name": "Our Food: Composition and Cooking",            "order": 2,  "chapter_no": 2},
    {"id": "nios-hs-3",  "name": "Meal Planning",                                "order": 3,  "chapter_no": 3},
    {"id": "nios-hs-4",  "name": "Preservation of Food",                         "order": 4,  "chapter_no": 4},
    {"id": "nios-hs-5",  "name": "Our Clothes: Fibre to Fabric",                 "order": 5,  "chapter_no": 5},
    {"id": "nios-hs-6",  "name": "Care and Maintenance of Clothes",              "order": 6,  "chapter_no": 6},
    {"id": "nios-hs-7",  "name": "The Child: Growth and Development",            "order": 7,  "chapter_no": 7},
    {"id": "nios-hs-8",  "name": "Childcare and Health",                         "order": 8,  "chapter_no": 8},
    {"id": "nios-hs-9",  "name": "Housing and Home Management",                  "order": 9,  "chapter_no": 9},
    {"id": "nios-hs-10", "name": "Consumer Education",                           "order": 10, "chapter_no": 10},
    {"id": "nios-hs-11", "name": "Family Resource Management",                   "order": 11, "chapter_no": 11},
    {"id": "nios-hs-12", "name": "Community Health and Hygiene",                 "order": 12, "chapter_no": 12},
]

_NIOS_INDIAN_CULTURE = [
    {"id": "nios-ich-1",  "name": "Introduction to Indian Culture and Heritage",  "order": 1,  "chapter_no": 1},
    {"id": "nios-ich-2",  "name": "The Harappan Civilisation",                    "order": 2,  "chapter_no": 2},
    {"id": "nios-ich-3",  "name": "The Vedic Age",                                "order": 3,  "chapter_no": 3},
    {"id": "nios-ich-4",  "name": "Indian Philosophy",                            "order": 4,  "chapter_no": 4},
    {"id": "nios-ich-5",  "name": "Art and Architecture in India",                "order": 5,  "chapter_no": 5},
    {"id": "nios-ich-6",  "name": "Folk and Classical Music",                     "order": 6,  "chapter_no": 6},
    {"id": "nios-ich-7",  "name": "Dance Forms of India",                         "order": 7,  "chapter_no": 7},
    {"id": "nios-ich-8",  "name": "Theatre and Drama",                            "order": 8,  "chapter_no": 8},
    {"id": "nios-ich-9",  "name": "Indian Handicrafts",                           "order": 9,  "chapter_no": 9},
    {"id": "nios-ich-10", "name": "Fairs and Festivals",                          "order": 10, "chapter_no": 10},
    {"id": "nios-ich-11", "name": "Languages and Literature",                     "order": 11, "chapter_no": 11},
    {"id": "nios-ich-12", "name": "Science and Technology in Ancient India",      "order": 12, "chapter_no": 12},
]

_NIOS_LOGISTICS = [
    {"id": "nios-log-1",  "name": "Introduction to Logistics",                   "order": 1,  "chapter_no": 1},
    {"id": "nios-log-2",  "name": "Transportation in Logistics",                 "order": 2,  "chapter_no": 2},
    {"id": "nios-log-3",  "name": "Warehousing and Storage",                     "order": 3,  "chapter_no": 3},
    {"id": "nios-log-4",  "name": "Inventory Management",                        "order": 4,  "chapter_no": 4},
    {"id": "nios-log-5",  "name": "Supply Chain Management",                     "order": 5,  "chapter_no": 5},
    {"id": "nios-log-6",  "name": "Documentation in Logistics",                  "order": 6,  "chapter_no": 6},
    {"id": "nios-log-7",  "name": "Packaging and Labelling",                     "order": 7,  "chapter_no": 7},
    {"id": "nios-log-8",  "name": "Logistics and Technology",                    "order": 8,  "chapter_no": 8},
]

_NIOS_MATHEMATICS = [
    {"id": "nios-mat-1",  "name": "Number Systems",                              "order": 1,  "chapter_no": 1},
    {"id": "nios-mat-2",  "name": "Polynomials",                                 "order": 2,  "chapter_no": 2},
    {"id": "nios-mat-3",  "name": "Linear Equations in Two Variables",           "order": 3,  "chapter_no": 3},
    {"id": "nios-mat-4",  "name": "Quadratic Equations",                         "order": 4,  "chapter_no": 4},
    {"id": "nios-mat-5",  "name": "Arithmetic Progressions",                     "order": 5,  "chapter_no": 5},
    {"id": "nios-mat-6",  "name": "Triangles and Congruence",                    "order": 6,  "chapter_no": 6},
    {"id": "nios-mat-7",  "name": "Coordinate Geometry",                         "order": 7,  "chapter_no": 7},
    {"id": "nios-mat-8",  "name": "Introduction to Trigonometry",                "order": 8,  "chapter_no": 8},
    {"id": "nios-mat-9",  "name": "Applications of Trigonometry",               "order": 9,  "chapter_no": 9},
    {"id": "nios-mat-10", "name": "Circles and Tangents",                        "order": 10, "chapter_no": 10},
    {"id": "nios-mat-11", "name": "Areas Related to Circles",                   "order": 11, "chapter_no": 11},
    {"id": "nios-mat-12", "name": "Surface Areas and Volumes",                   "order": 12, "chapter_no": 12},
    {"id": "nios-mat-13", "name": "Statistics",                                  "order": 13, "chapter_no": 13},
    {"id": "nios-mat-14", "name": "Probability",                                 "order": 14, "chapter_no": 14},
]

_NIOS_PAINTINGS = [
    {"id": "nios-pai-1",  "name": "Introduction to Painting",                    "order": 1,  "chapter_no": 1},
    {"id": "nios-pai-2",  "name": "Elements and Principles of Art",              "order": 2,  "chapter_no": 2},
    {"id": "nios-pai-3",  "name": "Indian Miniature Paintings",                  "order": 3,  "chapter_no": 3},
    {"id": "nios-pai-4",  "name": "Mughal and Rajput Paintings",                 "order": 4,  "chapter_no": 4},
    {"id": "nios-pai-5",  "name": "Modern Indian Paintings",                     "order": 5,  "chapter_no": 5},
    {"id": "nios-pai-6",  "name": "Techniques and Media",                        "order": 6,  "chapter_no": 6},
    {"id": "nios-pai-7",  "name": "Still Life and Nature Drawing",               "order": 7,  "chapter_no": 7},
    {"id": "nios-pai-8",  "name": "Composition and Perspective",                 "order": 8,  "chapter_no": 8},
]

_NIOS_PSYCHOLOGY = [
    {"id": "nios-psy-1",  "name": "Introduction to Psychology",                  "order": 1,  "chapter_no": 1},
    {"id": "nios-psy-2",  "name": "Methods of Psychology",                       "order": 2,  "chapter_no": 2},
    {"id": "nios-psy-3",  "name": "Biological Basis of Behaviour",               "order": 3,  "chapter_no": 3},
    {"id": "nios-psy-4",  "name": "Sensation and Perception",                    "order": 4,  "chapter_no": 4},
    {"id": "nios-psy-5",  "name": "Learning",                                    "order": 5,  "chapter_no": 5},
    {"id": "nios-psy-6",  "name": "Memory and Forgetting",                       "order": 6,  "chapter_no": 6},
    {"id": "nios-psy-7",  "name": "Thinking and Problem Solving",               "order": 7,  "chapter_no": 7},
    {"id": "nios-psy-8",  "name": "Intelligence and Creativity",                 "order": 8,  "chapter_no": 8},
    {"id": "nios-psy-9",  "name": "Motivation and Emotion",                      "order": 9,  "chapter_no": 9},
    {"id": "nios-psy-10", "name": "Personality",                                 "order": 10, "chapter_no": 10},
    {"id": "nios-psy-11", "name": "Stress and Coping",                          "order": 11, "chapter_no": 11},
    {"id": "nios-psy-12", "name": "Social Behaviour",                            "order": 12, "chapter_no": 12},
    {"id": "nios-psy-13", "name": "Psychological Disorders",                     "order": 13, "chapter_no": 13},
    {"id": "nios-psy-14", "name": "Applied Psychology",                          "order": 14, "chapter_no": 14},
]

_NIOS_SCIENCE = [
    {"id": "nios-sci-1",  "name": "Measurement in Science",                      "order": 1,  "chapter_no": 1},
    {"id": "nios-sci-2",  "name": "Motion and Force",                            "order": 2,  "chapter_no": 2},
    {"id": "nios-sci-3",  "name": "Work, Energy and Power",                      "order": 3,  "chapter_no": 3},
    {"id": "nios-sci-4",  "name": "Heat and Temperature",                        "order": 4,  "chapter_no": 4},
    {"id": "nios-sci-5",  "name": "Sound and Light",                             "order": 5,  "chapter_no": 5},
    {"id": "nios-sci-6",  "name": "Electricity and Magnetism",                   "order": 6,  "chapter_no": 6},
    {"id": "nios-sci-7",  "name": "Structure of Matter and Atom",                "order": 7,  "chapter_no": 7},
    {"id": "nios-sci-8",  "name": "Chemical Reactions",                          "order": 8,  "chapter_no": 8},
    {"id": "nios-sci-9",  "name": "Acids, Bases and Salts",                     "order": 9,  "chapter_no": 9},
    {"id": "nios-sci-10", "name": "Carbon and its Compounds",                    "order": 10, "chapter_no": 10},
    {"id": "nios-sci-11", "name": "Cell: The Unit of Life",                      "order": 11, "chapter_no": 11},
    {"id": "nios-sci-12", "name": "Life Processes",                              "order": 12, "chapter_no": 12},
    {"id": "nios-sci-13", "name": "Reproduction and Heredity",                   "order": 13, "chapter_no": 13},
    {"id": "nios-sci-14", "name": "Our Environment",                             "order": 14, "chapter_no": 14},
    {"id": "nios-sci-15", "name": "Technology in Daily Life",                    "order": 15, "chapter_no": 15},
    {"id": "nios-sci-16", "name": "Space Science",                               "order": 16, "chapter_no": 16},
]

_NIOS_SOCIAL_SCIENCE = [
    {"id": "nios-ss-1",  "name": "India and the World",                          "order": 1,  "chapter_no": 1},
    {"id": "nios-ss-2",  "name": "India: Physical Features",                     "order": 2,  "chapter_no": 2},
    {"id": "nios-ss-3",  "name": "Climate of India",                             "order": 3,  "chapter_no": 3},
    {"id": "nios-ss-4",  "name": "Natural Resources of India",                   "order": 4,  "chapter_no": 4},
    {"id": "nios-ss-5",  "name": "Agriculture in India",                         "order": 5,  "chapter_no": 5},
    {"id": "nios-ss-6",  "name": "Industries in India",                          "order": 6,  "chapter_no": 6},
    {"id": "nios-ss-7",  "name": "India's Freedom Struggle",                     "order": 7,  "chapter_no": 7},
    {"id": "nios-ss-8",  "name": "Constitutional Development of India",          "order": 8,  "chapter_no": 8},
    {"id": "nios-ss-9",  "name": "Indian Government: Union and State",           "order": 9,  "chapter_no": 9},
    {"id": "nios-ss-10", "name": "Local Self-Government",                        "order": 10, "chapter_no": 10},
    {"id": "nios-ss-11", "name": "Fundamental Rights and Duties",                "order": 11, "chapter_no": 11},
    {"id": "nios-ss-12", "name": "India's Foreign Policy",                       "order": 12, "chapter_no": 12},
    {"id": "nios-ss-13", "name": "Economic Development in India",                "order": 13, "chapter_no": 13},
    {"id": "nios-ss-14", "name": "Poverty and Unemployment",                     "order": 14, "chapter_no": 14},
    {"id": "nios-ss-15", "name": "India in the Global Economy",                  "order": 15, "chapter_no": 15},
]

_NIOS_WAREHOUSE = [
    {"id": "nios-wh-1",  "name": "Introduction to Warehousing",                  "order": 1,  "chapter_no": 1},
    {"id": "nios-wh-2",  "name": "Types of Warehouses",                          "order": 2,  "chapter_no": 2},
    {"id": "nios-wh-3",  "name": "Warehouse Operations",                         "order": 3,  "chapter_no": 3},
    {"id": "nios-wh-4",  "name": "Receiving and Dispatch",                       "order": 4,  "chapter_no": 4},
    {"id": "nios-wh-5",  "name": "Storage Systems and Equipment",                "order": 5,  "chapter_no": 5},
    {"id": "nios-wh-6",  "name": "Inventory Control",                            "order": 6,  "chapter_no": 6},
    {"id": "nios-wh-7",  "name": "Safety and Security in Warehouse",             "order": 7,  "chapter_no": 7},
    {"id": "nios-wh-8",  "name": "Warehouse Management Systems",                 "order": 8,  "chapter_no": 8},
]

_NIOS_SIGN_LANGUAGE = [
    {"id": "nios-isl-1",  "name": "Introduction to Indian Sign Language",        "order": 1,  "chapter_no": 1},
    {"id": "nios-isl-2",  "name": "Handshapes and Fingerspelling",               "order": 2,  "chapter_no": 2},
    {"id": "nios-isl-3",  "name": "Basic Vocabulary: Family and People",         "order": 3,  "chapter_no": 3},
    {"id": "nios-isl-4",  "name": "Basic Vocabulary: Objects and Actions",       "order": 4,  "chapter_no": 4},
    {"id": "nios-isl-5",  "name": "Numbers, Time and Calendar",                  "order": 5,  "chapter_no": 5},
    {"id": "nios-isl-6",  "name": "Sentence Structure in ISL",                   "order": 6,  "chapter_no": 6},
    {"id": "nios-isl-7",  "name": "Conversational Sign Language",                "order": 7,  "chapter_no": 7},
    {"id": "nios-isl-8",  "name": "Deaf Culture and Community",                  "order": 8,  "chapter_no": 8},
]

# ── Subject metadata (icon + color for UI) ────────────────────────────────────

_NIOS_SUBJECT_META = {
    "Accountancy":               ("TrendingUp",  "#10b981"),
    "Business Studies":          ("Briefcase",   "#3b82f6"),
    "Data Entry Operations":     ("Monitor",     "#6366f1"),
    "Economics":                 ("BarChart2",   "#f59e0b"),
    "English":                   ("BookOpen",    "#ec4899"),
    "Entrepreneurship":          ("Zap",         "#8b5cf6"),
    "Folk Art":                  ("Palette",     "#f97316"),
    "Home Science":              ("Home",        "#14b8a6"),
    "Indian Culture and Heritage":("Globe",      "#a855f7"),
    "Logistics":                 ("Truck",       "#0ea5e9"),
    "Mathematics":               ("Calculator",  "#22d3ee"),
    "Paintings":                 ("Paintbrush",  "#fb923c"),
    "Psychology":                ("Brain",       "#e879f9"),
    "Science and Technology":    ("Atom",        "#4ade80"),
    "Social Science":            ("Map",         "#60a5fa"),
    "Warehouse":                 ("Package",     "#facc15"),
    "Indian Sign Language":      ("Hand",        "#f87171"),
}

# ── Subject → chapters mapping ────────────────────────────────────────────────

NIOS_CURRICULUM: dict = {
    "Accountancy":                _NIOS_ACCOUNTANCY,
    "Business Studies":           _NIOS_BUSINESS_STUDIES,
    "Data Entry Operations":      _NIOS_DATA_ENTRY,
    "Economics":                  _NIOS_ECONOMICS,
    "English":                    _NIOS_ENGLISH,
    "Entrepreneurship":           _NIOS_ENTREPRENEURSHIP,
    "Folk Art":                   _NIOS_FOLK_ART,
    "Home Science":               _NIOS_HOME_SCIENCE,
    "Indian Culture and Heritage": _NIOS_INDIAN_CULTURE,
    "Logistics":                  _NIOS_LOGISTICS,
    "Mathematics":                _NIOS_MATHEMATICS,
    "Paintings":                  _NIOS_PAINTINGS,
    "Psychology":                 _NIOS_PSYCHOLOGY,
    "Science and Technology":     _NIOS_SCIENCE,
    "Social Science":             _NIOS_SOCIAL_SCIENCE,
    "Warehouse":                  _NIOS_WAREHOUSE,
    "Indian Sign Language":       _NIOS_SIGN_LANGUAGE,
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
