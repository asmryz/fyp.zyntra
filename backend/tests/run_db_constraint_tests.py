"""
Database-level constraint tests for ZYNTRA (migration 70e5d3631eb4).

Each case runs raw SQL directly against PostgreSQL, so it tests the database
constraints themselves, not the API validation. Everything happens inside one
transaction with a savepoint per case, and the transaction is rolled back at
the end: no test data is left in the database.

Run from the backend folder (virtual environment active):
    python tests/run_db_constraint_tests.py
"""
import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from database import engine  # noqa: E402

results = []


def check(name, ok, info=""):
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({info})" if info and not ok else ""))


def attempt(conn, sql, params=None):
    """Run one statement in a savepoint. Returns None if accepted, else the constraint name that rejected it."""
    savepoint = conn.begin_nested()
    try:
        conn.execute(text(sql), params or {})
        # Deferred unique constraints are only checked at commit; force the check now
        conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        savepoint.commit()
        return None
    except IntegrityError as error:
        savepoint.rollback()
        return getattr(error.orig.diag, "constraint_name", None) or str(error.orig).splitlines()[0]
    finally:
        conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))


def expect_rejected(conn, name, sql, constraint, params=None):
    result = attempt(conn, sql, params)
    check(f"{name}: rejected", result == constraint, f"got {result!r}")


def expect_accepted(conn, name, sql, params=None):
    result = attempt(conn, sql, params)
    check(f"{name}: accepted", result is None, f"rejected by {result!r}")


def main():
    conn = engine.connect()
    outer = conn.begin()
    try:
        insert_user = (
            "INSERT INTO users (full_name, email, password_hash, role) "
            "VALUES ('Constraint Test', :email, 'x', 'student') RETURNING id"
        )
        user_id = conn.execute(text(insert_user), {"email": "constraint.test.zyntra@example.org"}).scalar_one()
        profile_id = conn.execute(
            text("INSERT INTO student_profiles (user_id) VALUES (:u) RETURNING id"), {"u": user_id}
        ).scalar_one()
        program_id = conn.execute(text(
            "INSERT INTO programs (name, slug, status) VALUES ('Constraint Test Program', 'constraint-test-program', 'draft') "
            "RETURNING id"
        )).scalar_one()

        print("\nStudent percentage (ck_student_profiles_percentage_range)")
        upd = "UPDATE student_profiles SET percentage = :v WHERE id = :p"
        expect_rejected(conn, "percentage -1 (update)", upd, "ck_student_profiles_percentage_range", {"v": -1, "p": profile_id})
        expect_rejected(conn, "percentage 100.5 (update)", upd, "ck_student_profiles_percentage_range", {"v": 100.5, "p": profile_id})
        expect_rejected(conn, "percentage 101 (insert)",
                        "INSERT INTO student_profiles (user_id, percentage) VALUES (:u, 101)",
                        "ck_student_profiles_percentage_range", {"u": user_id})
        for value in (0, 72.5, 100):
            expect_accepted(conn, f"percentage {value}", upd, {"v": value, "p": profile_id})
        expect_accepted(conn, "percentage NULL (optional field)", upd, {"v": None, "p": profile_id})

        print("\nStudent marks (ck_student_profiles_marks_within_total / _not_negative)")
        marks = "UPDATE student_profiles SET obtained_marks = :o, total_marks = :t WHERE id = :p"
        expect_rejected(conn, "obtained 1101 > total 1100", marks, "ck_student_profiles_marks_within_total",
                        {"o": 1101, "t": 1100, "p": profile_id})
        expect_rejected(conn, "negative obtained marks", marks, "ck_student_profiles_marks_not_negative",
                        {"o": -5, "t": 1100, "p": profile_id})
        expect_rejected(conn, "negative total marks", marks, "ck_student_profiles_marks_not_negative",
                        {"o": None, "t": -1, "p": profile_id})
        expect_accepted(conn, "obtained 900 of 1100", marks, {"o": 900, "t": 1100, "p": profile_id})
        expect_accepted(conn, "obtained equal to total", marks, {"o": 1100, "t": 1100, "p": profile_id})
        expect_accepted(conn, "marks NULL (optional fields)", marks, {"o": None, "t": None, "p": profile_id})

        print("\nProgram minimum percentage (ck_programs_min_percentage_range)")
        prog = "UPDATE programs SET min_percentage = :v WHERE id = :p"
        expect_rejected(conn, "min_percentage -0.01", prog, "ck_programs_min_percentage_range", {"v": -0.01, "p": program_id})
        expect_rejected(conn, "min_percentage 150", prog, "ck_programs_min_percentage_range", {"v": 150, "p": program_id})
        expect_accepted(conn, "min_percentage 60", prog, {"v": 60, "p": program_id})

        print("\nTest topic titles (uq_test_topics_subject_title)")
        subject_a = conn.execute(text("INSERT INTO test_subjects (name, status) VALUES ('Constraint A', 'draft') RETURNING id")).scalar_one()
        subject_b = conn.execute(text("INSERT INTO test_subjects (name, status) VALUES ('Constraint B', 'draft') RETURNING id")).scalar_one()
        topic = "INSERT INTO test_topics (subject_id, title) VALUES (:s, :t)"
        expect_accepted(conn, "first 'Algebra' under subject A", topic, {"s": subject_a, "t": "Algebra"})
        expect_rejected(conn, "second 'Algebra' under subject A", topic, "uq_test_topics_subject_title", {"s": subject_a, "t": "Algebra"})
        expect_accepted(conn, "'Algebra' under subject B", topic, {"s": subject_b, "t": "Algebra"})
        expect_accepted(conn, "'Geometry' under subject A", topic, {"s": subject_a, "t": "Geometry"})
        expect_rejected(conn, "renaming 'Geometry' to 'Algebra' (update)",
                        "UPDATE test_topics SET title = 'Algebra' WHERE subject_id = :s AND title = 'Geometry'",
                        "uq_test_topics_subject_title", {"s": subject_a})

        print("\nRoadmap positions (uq_roadmap_nodes_branch_position / uq_roadmap_node_sections_node_position)")
        roadmap = conn.execute(text("INSERT INTO roadmaps (title, status) VALUES ('Constraint Roadmap', 'draft') RETURNING id")).scalar_one()
        branch = conn.execute(text("INSERT INTO roadmap_branches (roadmap_id, name) VALUES (:r, 'B1') RETURNING id"), {"r": roadmap}).scalar_one()
        other_branch = conn.execute(text("INSERT INTO roadmap_branches (roadmap_id, name, position) VALUES (:r, 'B2', 1) RETURNING id"), {"r": roadmap}).scalar_one()
        node_sql = "INSERT INTO roadmap_nodes (branch_id, title, position) VALUES (:b, :t, :p)"
        expect_accepted(conn, "step at position 0", node_sql, {"b": branch, "t": "Step A", "p": 0})
        expect_rejected(conn, "second step at position 0 in the same branch", node_sql, "uq_roadmap_nodes_branch_position",
                        {"b": branch, "t": "Step B", "p": 0})
        expect_accepted(conn, "position 0 in a different branch", node_sql, {"b": other_branch, "t": "Step C", "p": 0})
        expect_accepted(conn, "step at position 1", node_sql, {"b": branch, "t": "Step D", "p": 1})
        expect_rejected(conn, "moving a step onto an occupied position (update)",
                        "UPDATE roadmap_nodes SET position = 0 WHERE branch_id = :b AND title = 'Step D'",
                        "uq_roadmap_nodes_branch_position", {"b": branch})
        # A swap is valid at commit time even though it passes through a duplicate (deferred constraint)
        savepoint = conn.begin_nested()
        conn.execute(text("UPDATE roadmap_nodes SET position = 1 WHERE branch_id = :b AND title = 'Step A'"), {"b": branch})
        conn.execute(text("UPDATE roadmap_nodes SET position = 0 WHERE branch_id = :b AND title = 'Step D'"), {"b": branch})
        try:
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            savepoint.commit()
            check("swapping two steps inside one transaction: accepted (deferred check)", True)
        except IntegrityError as error:
            savepoint.rollback()
            check("swapping two steps inside one transaction: accepted (deferred check)", False, str(error.orig))
        finally:
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

        node = conn.execute(text("SELECT id FROM roadmap_nodes WHERE branch_id = :b AND title = 'Step A'"), {"b": branch}).scalar_one()
        section = ("INSERT INTO roadmap_node_sections (node_id, section_title, section_type, content, position) "
                   "VALUES (:n, :t, 'skills', '{}'::jsonb, :p)")
        expect_accepted(conn, "section at position 0", section, {"n": node, "t": "Skills", "p": 0})
        expect_rejected(conn, "second section at position 0 in the same step", section,
                        "uq_roadmap_node_sections_node_position", {"n": node, "t": "Tools", "p": 0})
        expect_accepted(conn, "section at position 1", section, {"n": node, "t": "Tools", "p": 1})

        print("\nResource types (ck_learning_resources_type)")
        resource = ("INSERT INTO learning_resources (subject_id, title, url, resource_type) "
                    "VALUES (:s, 'R', 'https://example.org', :t)")
        for kind in ("video", "article", "pdf", "link"):
            expect_accepted(conn, f"type '{kind}'", resource, {"s": subject_a, "t": kind})
        for kind in ("podcast", "platform", "past_paper", "VIDEO"):
            expect_rejected(conn, f"type '{kind}'", resource, "ck_learning_resources_type", {"s": subject_a, "t": kind})
        expect_rejected(conn, "changing a type to 'audio' (update)",
                        "UPDATE learning_resources SET resource_type = 'audio' WHERE subject_id = :s",
                        "ck_learning_resources_type", {"s": subject_a})

        print("\nCase-insensitive email (uq_users_email_lower)")
        expect_rejected(conn, "same email in different letter case", insert_user, "uq_users_email_lower",
                        {"email": "Constraint.Test.ZYNTRA@Example.org"})
        expect_rejected(conn, "same email in upper case", insert_user, "uq_users_email_lower",
                        {"email": "CONSTRAINT.TEST.ZYNTRA@EXAMPLE.ORG"})
        expect_accepted(conn, "a different email", insert_user, {"email": "constraint.test2.zyntra@example.org"})
        expect_rejected(conn, "changing an email to another user's address in a different case (update)",
                        "UPDATE users SET email = 'CONSTRAINT.TEST.ZYNTRA@example.org' WHERE email = 'constraint.test2.zyntra@example.org'",
                        "uq_users_email_lower")
    finally:
        outer.rollback()
        conn.close()

    passed = sum(results)
    print(f"\n{passed}/{len(results)} database constraint checks passed (all test rows rolled back)")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
