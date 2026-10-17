import re
from typing import Dict, List, Optional, Set

# Canonical mapping for common skills and technologies.
# Prevents false negatives (e.g., "React.js" vs "React", "Postgres" vs "PostgreSQL").
# Explicitly avoids conflating false friends (e.g. Java vs JavaScript, C vs C++).

CANONICAL_ALIASES: Dict[str, str] = {
    # JavaScript ecosystem
    "js": "JavaScript",
    "javascript": "JavaScript",
    "vanilla js": "JavaScript",
    "vanilla javascript": "JavaScript",
    "es6": "JavaScript",
    "es6+": "JavaScript",
    "modern javascript": "JavaScript",

    # TypeScript
    "ts": "TypeScript",
    "typescript": "TypeScript",

    # Python
    "python": "Python",
    "python3": "Python",
    "py": "Python",

    # React
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "react native": "React Native",

    # Node.js
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",

    # Next.js
    "next": "Next.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",

    # Express
    "express": "Express.js",
    "express.js": "Express.js",
    "expressjs": "Express.js",

    # FastAPI
    "fastapi": "FastAPI",
    "fast-api": "FastAPI",

    # Flask / Django
    "flask": "Flask",
    "django": "Django",

    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "sqlite3": "SQLite",
    "supabase": "Supabase",
    "prisma": "Prisma ORM",
    "prisma orm": "Prisma ORM",
    "sqlalchemy": "SQLAlchemy",

    # APIs & Web architecture
    "rest": "REST API",
    "rest api": "REST API",
    "rest apis": "REST API",
    "restful": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "restful api development": "REST API",
    "rest api development": "REST API",
    "graphql": "GraphQL",
    "websocket": "WebSockets",
    "websockets": "WebSockets",

    # DevOps & Containers
    "docker": "Docker",
    "dockerfile": "Docker",
    "docker-compose": "Docker",
    "docker compose": "Docker",
    "docker containerization": "Docker",
    "containers": "Docker",
    "containerization": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "continuous integration": "CI/CD",
    "continuous delivery": "CI/CD",
    "github actions": "GitHub Actions",
    "gh actions": "GitHub Actions",

    # Cloud platforms
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",

    # Styling & Frontend
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "css": "CSS",
    "css3": "CSS",
    "html": "HTML",
    "html5": "HTML",

    # Testing & QA
    "unit test": "Unit Testing",
    "unit tests": "Unit Testing",
    "unit testing": "Unit Testing",
    "pytest": "Pytest",
    "jest": "Jest",
    "vitest": "Vitest",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "testing": "Testing",

    # Version Control
    "git": "Git",
    "github": "Git",
    "version control": "Git",

    # Core Engineering Disciplines & Concepts
    "software engineering": "Software Engineering",
    "software development": "Software Engineering",
    "software developer": "Software Engineering",
    "software engineer": "Software Engineering",
    "swe": "Software Engineering",
    "sde": "Software Engineering",
    "programming": "Software Engineering",
    "computer science": "Software Engineering",
    "web development": "Web Development",
    "full stack": "Full Stack Development",
    "full stack development": "Full Stack Development",
    "full-stack development": "Full Stack Development",
    "backend development": "Backend Development",
    "frontend development": "Frontend Development",
}


def sanitize_skill_string(s: str) -> str:
    """Strips outer whitespace and lowercases string for lookup."""
    return s.strip().lower()


def normalize_skill_name(raw_name: str) -> str:
    """
    Normalizes a skill or technology name into its canonical display format.
    If the name is in CANONICAL_ALIASES, returns the canonical name.
    Otherwise, cleans extra spaces and returns title/cleaned casing.
    """
    if not raw_name or not raw_name.strip():
        return "Unknown"

    cleaned = sanitize_skill_string(raw_name)

    # 1. Exact alias match
    if cleaned in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[cleaned]

    # 2. Check without trailing punctuation or version numbers (e.g. 'python 3.11' -> 'Python')
    version_strip = re.sub(r"\s+v?\d+(\.\d+)*$", "", cleaned)
    if version_strip in CANONICAL_ALIASES:
        return CANONICAL_ALIASES[version_strip]

    # 3. Clean up formatting (e.g. capitalize words if no alias exists)
    return raw_name.strip()


def are_skills_equivalent(skill_a: str, skill_b: str) -> bool:
    """
    Checks if two skill strings refer to the same technology.
    Strictly forbids false-friend equivalence (e.g. Java and JavaScript).
    """
    norm_a = normalize_skill_name(skill_a).lower()
    norm_b = normalize_skill_name(skill_b).lower()

    if norm_a == norm_b:
        return True

    # Exact sanitized comparison
    clean_a = sanitize_skill_string(skill_a)
    clean_b = sanitize_skill_string(skill_b)
    if clean_a == clean_b:
        return True

    # Check alias canonical mapping
    canon_a = CANONICAL_ALIASES.get(clean_a)
    canon_b = CANONICAL_ALIASES.get(clean_b)
    if canon_a and canon_b and canon_a.lower() == canon_b.lower():
        return True

    # Strict false-friend protection
    false_friends = [
        {"java", "javascript"},
        {"c", "c++"},
        {"c", "c#"},
        {"c++", "c#"},
        {"rust", "ruby"},
        {"r", "react"},
        {"go", "google cloud"},
    ]
    pair = {clean_a, clean_b}
    for ff in false_friends:
        if ff == pair:
            return False

    return False


def skill_keyword_match(requirement_skill: str, evidence_text: str) -> bool:
    """
    Word-boundary regex match to check if a skill name appears in an evidence summary or excerpt.
    Prevents substring collisions (e.g., 'Java' matching in 'JavaScript').
    """
    if not requirement_skill or not evidence_text:
        return False

    norm_skill = normalize_skill_name(requirement_skill)
    # Target patterns
    patterns_to_check = {re.escape(requirement_skill.strip()), re.escape(norm_skill)}

    # Add canonical key if exists
    for alias, canon in CANONICAL_ALIASES.items():
        if canon.lower() == norm_skill.lower():
            patterns_to_check.add(re.escape(alias))

    for pat in patterns_to_check:
        regex = rf"(?<!\w){pat}(?!\w)"
        if re.search(regex, evidence_text, re.IGNORECASE):
            return True

    return False
