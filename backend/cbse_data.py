"""
NCERT Grade 8 Syllabus Data — Brooklyn National Public School (BNPS)
Chapter names and lessons match the official NCERT 2024-25 textbooks:
  Science        → Curiosity           (hecu1), 13 chapters
  Mathematics    → Ganita Prakash Pt1+Pt2 (hegp1/hegp2), 16 chapters
  Social Science → Exploring Society   (hees1), 7 chapters
"""

CBSE_SYLLABUS = {
    "8": {
        "Science": {
            "icon": "atom",
            "color": "#8b5cf6",
            "chapters": [
                {
                    "id": "c8s1",
                    "name": "Exploring the Investigative World of Science",
                    "lessons": [
                        "Scientific Method and Inquiry",
                        "Observation, Hypothesis and Experimentation",
                        "Variables and Controls",
                        "Data Collection and Analysis",
                    ],
                },
                {
                    "id": "c8s2",
                    "name": "The Invisible Living World: Beyond Our Naked Eye",
                    "lessons": [
                        "Microorganisms and Their Types",
                        "Bacteria: Structure and Functions",
                        "Viruses and Fungi",
                        "Protozoa and Algae",
                    ],
                },
                {
                    "id": "c8s3",
                    "name": "Health: The Ultimate Treasure",
                    "lessons": [
                        "Definition and Dimensions of Health",
                        "Communicable and Non-Communicable Diseases",
                        "Prevention and Hygiene",
                        "Immunity and Vaccination",
                    ],
                },
                {
                    "id": "c8s4",
                    "name": "Electricity: Magnetic and Heating Effects",
                    "lessons": [
                        "Magnetic Effect of Electric Current",
                        "Electromagnets and Their Uses",
                        "Heating Effect of Current",
                        "Electric Fuse and Safety",
                    ],
                },
                {
                    "id": "c8s5",
                    "name": "Exploring Forces",
                    "lessons": [
                        "Contact and Non-Contact Forces",
                        "Friction: Types and Applications",
                        "Gravitational Force",
                        "Pressure and Its Effects",
                    ],
                },
                {
                    "id": "c8s6",
                    "name": "Pressure, Winds, Storms, and Cyclones",
                    "lessons": [
                        "Atmospheric Pressure",
                        "How Winds are Formed",
                        "Thunderstorms and Lightning",
                        "Cyclones: Formation and Safety",
                    ],
                },
                {
                    "id": "c8s7",
                    "name": "Particulate Nature of Matter",
                    "lessons": [
                        "States of Matter",
                        "Molecules and Atoms",
                        "Kinetic Theory of Matter",
                        "Changes of State: Melting, Boiling, Evaporation",
                    ],
                },
                {
                    "id": "c8s8",
                    "name": "Nature of Matter: Elements, Compounds, and Mixtures",
                    "lessons": [
                        "Elements and Their Properties",
                        "Compounds vs Elements",
                        "Types of Mixtures",
                        "Separation Techniques",
                    ],
                },
                {
                    "id": "c8s9",
                    "name": "The Amazing World of Solutes, Solvents and Solutions",
                    "lessons": [
                        "Solutes and Solvents",
                        "Types of Solutions",
                        "Concentration and Solubility",
                        "Saturated and Unsaturated Solutions",
                    ],
                },
                {
                    "id": "c8s10",
                    "name": "Light: Mirrors and Lenses",
                    "lessons": [
                        "Laws of Reflection",
                        "Plane and Spherical Mirrors",
                        "Refraction of Light",
                        "Convex and Concave Lenses",
                    ],
                },
                {
                    "id": "c8s11",
                    "name": "Keeping Time with the Skies",
                    "lessons": [
                        "The Solar System",
                        "Day, Night and Seasons",
                        "Moon Phases and Calendars",
                        "Tides and Their Causes",
                    ],
                },
                {
                    "id": "c8s12",
                    "name": "How Nature Works in Harmony",
                    "lessons": [
                        "Ecosystems and Their Components",
                        "Food Chains and Food Webs",
                        "Biodiversity and Conservation",
                        "Environmental Balance",
                    ],
                },
                {
                    "id": "c8s13",
                    "name": "Our Home: Earth, a Unique Life Sustaining Planet",
                    "lessons": [
                        "Earth's Unique Features",
                        "The Atmosphere and Its Layers",
                        "Water Cycle and Hydrosphere",
                        "Climate and Human Impact",
                    ],
                },
            ],
        },

        "Mathematics": {
            "icon": "calculator",
            "color": "#22d3ee",
            "chapters": [
                {
                    "id": "c8m1",
                    "name": "Rational Numbers",
                    "lessons": [
                        "Properties of Rational Numbers",
                        "Representation on Number Line",
                        "Rational Numbers Between Two Rationals",
                        "Operations on Rational Numbers",
                    ],
                },
                {
                    "id": "c8m2",
                    "name": "Exponents and Powers",
                    "lessons": [
                        "Powers with Negative Exponents",
                        "Laws of Exponents",
                        "Standard Form (Scientific Notation)",
                        "Applications of Exponents",
                    ],
                },
                {
                    "id": "c8m3",
                    "name": "Squares and Square Roots",
                    "lessons": [
                        "Perfect Squares and Properties",
                        "Finding Square Roots",
                        "Square Roots of Decimals and Fractions",
                        "Estimating Square Roots",
                    ],
                },
                {
                    "id": "c8m4",
                    "name": "Cubes and Cube Roots",
                    "lessons": [
                        "Perfect Cubes",
                        "Cube Root by Prime Factorization",
                        "Cube Root of Large Numbers",
                        "Applications",
                    ],
                },
                {
                    "id": "c8m5",
                    "name": "Playing with Numbers",
                    "lessons": [
                        "Numbers in General Form",
                        "Games with Numbers",
                        "Divisibility Rules",
                        "Letters for Digits",
                    ],
                },
                {
                    "id": "c8m6",
                    "name": "Algebraic Expressions and Identities",
                    "lessons": [
                        "Terms, Factors and Coefficients",
                        "Multiplication of Algebraic Expressions",
                        "Standard Identities",
                        "Applying Identities",
                    ],
                },
                {
                    "id": "c8m7",
                    "name": "Factorisation",
                    "lessons": [
                        "Factors of Natural Numbers",
                        "Factorisation by Common Factors",
                        "Factorisation by Regrouping",
                        "Division of Algebraic Expressions",
                    ],
                },
                {
                    "id": "c8m8",
                    "name": "Linear Equations in One Variable",
                    "lessons": [
                        "Solving Linear Equations",
                        "Equations with Variables on Both Sides",
                        "Reducing Equations",
                        "Word Problems",
                    ],
                },
                {
                    "id": "c8m9",
                    "name": "Comparing Quantities",
                    "lessons": [
                        "Ratios and Percentages",
                        "Increase and Decrease Percentage",
                        "Profit, Loss and Discount",
                        "Simple and Compound Interest",
                    ],
                },
                {
                    "id": "c8m10",
                    "name": "Direct and Indirect Variations",
                    "lessons": [
                        "Direct Proportion",
                        "Inverse Proportion",
                        "Unitary Method",
                        "Real-Life Applications",
                    ],
                },
                {
                    "id": "c8m11",
                    "name": "Understanding Quadrilaterals",
                    "lessons": [
                        "Types of Quadrilaterals",
                        "Angle Sum Property",
                        "Properties of Parallelograms",
                        "Rhombus, Rectangle and Square",
                    ],
                },
                {
                    "id": "c8m12",
                    "name": "Visualising Solid Shapes",
                    "lessons": [
                        "Faces, Edges and Vertices",
                        "Nets of Solid Shapes",
                        "Drawing Solids on Flat Surfaces",
                        "Euler's Formula",
                    ],
                },
                {
                    "id": "c8m13",
                    "name": "Practical Geometry",
                    "lessons": [
                        "Constructing Quadrilaterals",
                        "Given Four Sides and a Diagonal",
                        "Given Two Diagonals and Three Sides",
                        "Special Quadrilaterals",
                    ],
                },
                {
                    "id": "c8m14",
                    "name": "Mensuration",
                    "lessons": [
                        "Area of Trapezium",
                        "Area of General Quadrilaterals and Polygons",
                        "Surface Area of Cube, Cuboid and Cylinder",
                        "Volume of Cube, Cuboid and Cylinder",
                    ],
                },
                {
                    "id": "c8m15",
                    "name": "Introduction to Graphs",
                    "lessons": [
                        "Bar Graphs and Histograms",
                        "Line Graphs",
                        "Pie Charts",
                        "Plotting on a Coordinate Plane",
                    ],
                },
                {
                    "id": "c8m16",
                    "name": "Data Handling",
                    "lessons": [
                        "Organising and Grouping Data",
                        "Mean, Median and Mode",
                        "Chance and Probability",
                        "Random Experiments",
                    ],
                },
            ],
        },

        "Social Science": {
            "icon": "globe",
            "color": "#3b82f6",
            "chapters": [
                {
                    "id": "c8ss1",
                    "name": "Natural Resources: Treasures of The Earth",
                    "lessons": [
                        "Types of Natural Resources",
                        "Land and Soil Resources",
                        "Water Resources",
                        "Conservation of Natural Resources",
                    ],
                },
                {
                    "id": "c8ss2",
                    "name": "The Changing Political Landscape of India",
                    "lessons": [
                        "Political Changes in Medieval India",
                        "Mughal Empire and Its Decline",
                        "Emergence of Regional Powers",
                        "British Expansion in India",
                    ],
                },
                {
                    "id": "c8ss3",
                    "name": "The Rise of the Marathas",
                    "lessons": [
                        "Origins of the Maratha Power",
                        "Shivaji and the Maratha Empire",
                        "Peshwa Administration",
                        "Maratha Confederacy and Decline",
                    ],
                },
                {
                    "id": "c8ss4",
                    "name": "The Colonial Transformation of India",
                    "lessons": [
                        "Establishment of British Rule",
                        "Economic Impact of Colonialism",
                        "Social and Cultural Changes",
                        "Resistance and Revolt of 1857",
                    ],
                },
                {
                    "id": "c8ss5",
                    "name": "From Ballot to Bharat: The Spirit of Universal Franchise",
                    "lessons": [
                        "Meaning and Importance of Universal Franchise",
                        "History of Voting Rights in India",
                        "Elections: Process and Significance",
                        "Role of the Election Commission",
                    ],
                },
                {
                    "id": "c8ss6",
                    "name": "The Parliamentary System: Legislature and Executive",
                    "lessons": [
                        "The Parliament of India",
                        "Lok Sabha and Rajya Sabha",
                        "The Executive: President and Prime Minister",
                        "How Laws are Made",
                    ],
                },
                {
                    "id": "c8ss7",
                    "name": "Resources at Work",
                    "lessons": [
                        "Human Resources",
                        "Land Use and Agriculture",
                        "Industries and Manufacturing",
                        "Sustainable Development",
                    ],
                },
            ],
        },
    }
}


def get_syllabus(class_level: str) -> dict:
    """Return the full subject dict for a class level, or {}."""
    return CBSE_SYLLABUS.get(str(class_level), {})


def get_classes() -> list[str]:
    """Return list of available class levels."""
    return list(CBSE_SYLLABUS.keys())


def get_subjects(class_level: str) -> list[str]:
    """Return list of subject names for a class level."""
    return list(CBSE_SYLLABUS.get(str(class_level), {}).keys())


def get_subject_meta(class_level: str, subject: str) -> dict:
    """Return icon/color metadata for a subject."""
    cls_data = CBSE_SYLLABUS.get(str(class_level), {})
    _aliases = {
        "maths": "Mathematics", "math": "Mathematics",
        "science": "Science",
        "social": "Social Science", "sst": "Social Science",
        "social_science": "Social Science", "social studies": "Social Science",
        "social science": "Social Science",
    }
    subj_key = _aliases.get(subject.lower().strip(), subject)
    data = cls_data.get(subj_key, {})
    return {"icon": data.get("icon", "book"), "color": data.get("color", "#94a3b8")}


def get_chapters(class_level: str, subject: str) -> list[dict]:
    """Return list of chapter dicts for class+subject, or []."""
    cls_data = CBSE_SYLLABUS.get(str(class_level), {})

    # Normalise subject name
    _aliases = {
        "maths": "Mathematics", "math": "Mathematics",
        "science": "Science",
        "social": "Social Science", "sst": "Social Science",
        "social_science": "Social Science", "social studies": "Social Science",
        "social science": "Social Science",
    }
    subj_key = _aliases.get(subject.lower().strip(), subject)

    subject_data = cls_data.get(subj_key, {})
    return subject_data.get("chapters", [])


def get_chapter_names(class_level: str, subject: str) -> list[str]:
    """Return just the chapter name strings."""
    return [c["name"] for c in get_chapters(class_level, subject)]
