"""
Insert clearly labelled placeholder content so every page has something to
display before the real SZABIST content is added.

None of this is official SZABIST information. Every placeholder title starts
with "[Placeholder]" and can be edited or deleted from the admin dashboard.

Usage (from the backend folder, virtual environment active):
    python seed_placeholders.py            add placeholders (skips ones that exist)
    python seed_placeholders.py --remove   delete placeholders that were not edited
"""
import sys

from database import SessionLocal
from app.models import (
    LearningResource, Program, Roadmap, RoadmapBranch, RoadmapNode, RoadmapNodeSection, Scholarship, SiteContent,
    TestSubject, TestTopic,
)

MARK = "[Placeholder]"

SITE_CONTENT = [
    ("about_szabist", "About SZABIST",
     f"{MARK} Shaheed Zulfikar Ali Bhutto Institute of Science and Technology (SZABIST) offers academic programs "
     "across multiple disciplines. Replace this paragraph with the official SZABIST introduction."),
    ("why_zyntra", "Why ZYNTRA exists",
     "Admission requirements, eligibility rules, program details, scholarship information and admission-test "
     "preparation material are often spread across many sources. ZYNTRA brings source-based guidance into one "
     "place so prospective students can understand what is required, check their preliminary eligibility, "
     "prepare for the admission test and plan their academic future with confidence."),
    ("admission_guidance", "General admission guidance",
     f"{MARK} Add general admission guidance here, such as the admission cycle, application steps and official "
     "contact points. Always refer students to official SZABIST sources for final information."),
    ("contact_email", "Email", f"{MARK} contact email address"),
    # The phone holds digits only (database CHECK), so it starts empty and is hidden until set
    ("contact_phone", "Phone", ""),
]


def add_site_content(db):
    for key, title, body in SITE_CONTENT:
        if db.query(SiteContent).filter(SiteContent.key == key).first() is None:
            db.add(SiteContent(key=key, title=title, body=body, status="published"))


def add_program(db):
    name = f"{MARK} BS Computer Science"
    program = db.query(Program).filter(Program.name == name).first()
    if program:
        return program
    program = Program(
        name=name,
        slug="placeholder-bs-computer-science",
        department="Computer Science",
        degree_level="Undergraduate",
        summary="Sample program record. Official program details will be added by the ZYNTRA administrator.",
        description=f"{MARK} Add the official program description here.",
        admission_requirements=f"{MARK} Add the official admission requirements here.",
        eligibility_notes="Eligibility criteria have not been published yet.",
        status="published",
    )
    db.add(program)
    db.flush()
    return program


def add_scholarship(db):
    title = f"{MARK} Sample Scholarship"
    if db.query(Scholarship).filter(Scholarship.title == title).first():
        return
    db.add(Scholarship(
        title=title,
        scholarship_type="Sample type",
        summary="This sample shows how scholarship information is presented. It is not a real scholarship.",
        description="Replace this record with official SZABIST scholarship details supplied for ZYNTRA.",
        eligibility_criteria=["Sample eligibility criterion 1", "Sample eligibility criterion 2"],
        benefits=["Sample benefit 1", "Sample benefit 2"],
        required_documents=["Sample document 1", "Sample document 2", "Sample document 3"],
        application_steps=[
            {"title": "Check eligibility", "description": "Sample step: describe how students confirm they qualify."},
            {"title": "Prepare documents", "description": "Sample step: describe which documents to gather."},
            {"title": "Submit application", "description": "Sample step: describe where and how to apply."},
            {"title": "Review", "description": "Sample step: describe how applications are assessed."},
            {"title": "Outcome", "description": "Sample step: describe how students are informed."},
        ],
        conditions=["Sample condition: replace with official terms."],
        status="published",
    ))


def add_roadmap(db, program):
    title = f"{MARK} Computer Science Career Roadmap"
    if db.query(Roadmap).filter(Roadmap.title == title).first():
        return
    roadmap = Roadmap(
        title=title,
        description="This roadmap demonstrates the layout only. The real roadmap content will be provided later.",
        program_id=program.id,
        status="published",
    )
    db.add(roadmap)
    db.flush()

    note = "Sample step. Replace with the roadmap content supplied for ZYNTRA."
    # (branch name, colour, [(step title, sample skills, sample tools)])
    sample = [
        ("Software Development", "#2563EB", [
            ("Programming fundamentals", ["Problem solving", "Basic algorithms"], ["Python", "Git"]),
            ("Web development", ["HTML and CSS", "APIs"], ["React"]),
        ]),
        ("Data Science", "#16A34A", [
            ("Statistics basics", ["Descriptive statistics"], ["Python", "Jupyter"]),
            ("Data analysis", ["Cleaning data", "Visualisation"], ["Jupyter"]),
        ]),
        ("Cybersecurity", "#EA580C", [
            ("Networking basics", ["How networks work"], []),
        ]),
    ]
    for branch_position, (name, color, steps) in enumerate(sample):
        branch = RoadmapBranch(roadmap_id=roadmap.id, name=name, color=color, position=branch_position,
                               description="Sample branch.")
        db.add(branch)
        db.flush()
        for step_position, (step_title, skills, tools) in enumerate(steps):
            node = RoadmapNode(branch_id=branch.id, title=step_title, description=note, position=step_position)
            node.sections = [RoadmapNodeSection(section_title="Skills", section_type="skills",
                                                content={"items": skills}, position=0)]
            if tools:
                node.sections.append(RoadmapNodeSection(section_title="Tools & Technologies", section_type="tools",
                                                        content={"items": tools}, position=1))
            db.add(node)


def add_test_prep(db):
    name = f"{MARK} Sample Mathematics"
    if db.query(TestSubject).filter(TestSubject.name == name).first():
        return
    subject = TestSubject(
        name=name,
        description="Sample subject showing how topics and learning resources appear. "
                    "It is not official admission-test material.",
        status="published",
    )
    db.add(subject)
    db.flush()

    topic = TestTopic(
        subject_id=subject.id,
        title="Sample topic: Basic arithmetic and algebra",
        explanation="Sample explanation. Replace with the topic explanation prepared for ZYNTRA.",
        status="published",
        sort_order=1,
    )
    db.add(topic)
    db.flush()

    db.add(LearningResource(
        subject_id=subject.id, topic_id=topic.id, title="Example resource: Khan Academy Math",
        url="https://www.khanacademy.org/math", resource_type="link",
        description="Example link showing how learning resources appear.",
    ))


def remove_placeholders(db):
    removed = 0
    for model, column in [(Program, Program.name), (Scholarship, Scholarship.title),
                          (Roadmap, Roadmap.title), (TestSubject, TestSubject.name)]:
        removed += db.query(model).filter(column.startswith(MARK)).delete(synchronize_session=False)
    # Website blocks are removed only if their text was never edited
    removed += db.query(SiteContent).filter(SiteContent.body.startswith(MARK)).delete(synchronize_session=False)
    db.commit()
    print(f"Removed {removed} placeholder record(s).")


def main():
    db = SessionLocal()
    try:
        if "--remove" in sys.argv:
            remove_placeholders(db)
            return
        add_site_content(db)
        program = add_program(db)
        add_scholarship(db)
        add_roadmap(db, program)
        add_test_prep(db)
        db.commit()
        print("Placeholder content added. Edit or delete it from the admin dashboard.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
