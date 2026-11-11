"""
Fixed values shared across the backend. The frontend reads the ones it needs
from GET /api/public/form-options so the lists are defined in one place.
"""


class Role:
    ROOT_ADMIN = "root_admin"
    STAFF = "staff"
    STUDENT = "student"

    ALL = (ROOT_ADMIN, STAFF, STUDENT)


class Status:
    DRAFT = "draft"
    PUBLISHED = "published"

    ALL = (DRAFT, PUBLISHED)


# Content modules that staff permissions are assigned for
CONTENT_MODULES = {
    "programs": "Program Information",
    "scholarships": "Scholarship Management",
    "roadmaps": "Roadmap Management",
    "test_prep": "Test Preparation Management",
    "site_content": "General Website Content",
}


class AccessLevel:
    READ = "read"              # view all content in the module
    WRITE = "write"            # create content, and edit/delete only their own
    READ_WRITE = "read_write"  # view, create, edit and delete all content

    ALL = (READ, WRITE, READ_WRITE)


ACCESS_LEVEL_LABELS = {
    AccessLevel.READ: "Read",
    AccessLevel.WRITE: "Write",
    AccessLevel.READ_WRITE: "Read + Write",
}


class CodePurpose:
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


# General education categories used by the student profile and by the
# program eligibility criteria. These are not SZABIST policy; admins choose
# which of them a program accepts.
# Allowed range of every "Display order" (sort_order) field: programs,
# scholarships, test subjects, topics and learning resources
DISPLAY_ORDER_MIN = 1
DISPLAY_ORDER_MAX = 100

# Input size limits shared by the API schemas (the frontend mirrors them in
# src/utils/limits.js). Long texts are descriptions, explanations and similar;
# the longest stored value when these were introduced was under 1,000 characters.
LONG_TEXT_MAX = 10_000
LIST_ITEM_MAX = 500        # one line of a list such as eligibility criteria
LIST_MAX_ITEMS = 50
MARKS_MAX = 100_000        # obtained / total marks
SEARCH_MAX = 100           # admin search boxes
MAX_REQUEST_BYTES = 1_000_000  # whole JSON request body

# Website contact phone: digits only, optionally starting with + (country code).
# Stored as text so leading zeros and the + are kept.
PHONE_PATTERN = r"^\+?[0-9]{7,15}$"

QUALIFICATIONS = [
    "Intermediate (HSSC)",
    "A-Levels",
    "Diploma of Associate Engineering (DAE)",
    "Bachelor's degree (14 years)",
    "Bachelor's degree (16 years)",
    "Master's degree",
    "Other",
]

# Kinds of blocks a roadmap step's detail card can contain. Admins can add
# any number of them, in any order, with their own titles.
ROADMAP_SECTION_TYPES = {
    "skills": "Skills (green tags)",
    "tools": "Tools & technologies (outlined tags)",
    "list": "Bullet list",
    "text": "Paragraph",
    "links": "Links",
}

# Suggested branch colours (blue, green, purple, orange, pink, red). Any hex
# colour can be chosen; these are offered first and used for migrated data.
ROADMAP_BRANCH_COLORS = ["#2563EB", "#16A34A", "#9333EA", "#EA580C", "#DB2777", "#DC2626"]

# Must match the ck_learning_resources_type constraint on learning_resources
RESOURCE_TYPES = {
    "video": "Video",
    "article": "Article / Notes",
    "pdf": "PDF / Past Paper",
    "link": "Link / Learning Platform",
}

# Website content keys the frontend knows how to display
SITE_CONTENT_KEYS = {
    "about_szabist": "Landing page: About SZABIST",
    "why_zyntra": "Landing page: Why ZYNTRA exists",
    "admission_guidance": "Student dashboard: General admission guidance",
    "contact_email": "Footer: Contact email",
    "contact_phone": "Footer: Contact phone",
}
