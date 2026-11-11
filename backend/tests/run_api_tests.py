"""
End-to-end API tests for ZYNTRA (standard library only, no extra packages).

What it does:
  1. Starts the backend on port 8765 with EMAIL_BACKEND=outbox, so emails are
     written to backend/dev_outbox/ instead of being sent.
  2. Runs the authentication, permission, content and student flows against
     the real Neon database.
  3. Deletes every user, invitation, content record and audit entry it created.

Test accounts use plus-addresses of the project mailbox
(zyntra.szabist+...@gmail.com), so nothing could reach a real person.

Run from the backend folder (virtual environment active):
    python tests/run_api_tests.py
"""
import json
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import timedelta
from http.cookiejar import CookieJar
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from database import SessionLocal  # noqa: E402
from app.core.security import utcnow  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog, Program, Roadmap, Scholarship, StaffInvitation, TestSubject, User,
)
from app.services.auth_service import create_root_admin  # noqa: E402

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
RUN_ID = secrets.token_hex(3)
OUTBOX = BACKEND_DIR / "dev_outbox"
SERVER_LOG = OUTBOX / "test_server.log"
PASSWORD = "TestPass123"

results = []


def check(name, condition, info=""):
    results.append((name, bool(condition)))
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}" + (f"  ({info})" if info and not condition else ""))


def test_email(label):
    return f"zyntra.szabist+t{RUN_ID}{label}@gmail.com"


class Client:
    """A tiny HTTP client that keeps cookies (like one browser) and a bearer token."""

    def __init__(self):
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
        self.token = None

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, timeout=60) as response:
                return response.status, json.loads(response.read() or b"null")
        except urllib.error.HTTPError as error:
            raw = error.read()
            try:
                return error.code, json.loads(raw)
            except json.JSONDecodeError:
                return error.code, raw.decode(errors="replace")

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body=None):
        return self.request("POST", path, body or {})

    def put(self, path, body):
        return self.request("PUT", path, body)

    def patch(self, path, body):
        return self.request("PATCH", path, body)

    def delete(self, path):
        return self.request("DELETE", path)

    def login(self, email, password):
        status, data = self.post("/api/auth/login", {"email": email, "password": password})
        if status == 200:
            self.token = data["access_token"]
        return status, data


def latest_email(to_address):
    files = sorted(OUTBOX.glob(f"*_{to_address.replace('@', '_at_')}.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text(encoding="utf-8"))


def code_from_email(to_address):
    email = latest_email(to_address)
    match = re.search(r"\b(\d{6})\b", email["text"]) if email else None
    return match.group(1) if match else None


def detail(data):
    return data.get("detail") if isinstance(data, dict) else data


def start_server():
    env = dict(os.environ, EMAIL_BACKEND="outbox")
    OUTBOX.mkdir(exist_ok=True)
    log_file = open(SERVER_LOG, "w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=BACKEND_DIR, env=env, stdout=log_file, stderr=subprocess.STDOUT,
    )
    for _ in range(60):
        try:
            with urllib.request.urlopen(BASE + "/api/health", timeout=2):
                return process
        except OSError:
            time.sleep(0.5)
    process.terminate()
    raise RuntimeError(f"Backend did not start. See {SERVER_LOG}")


# ---------------------------------------------------------------------------

def test_student_auth():
    print("\nStudent registration, verification and login")
    student = Client()
    email = test_email("stu")

    status, data = student.post("/api/auth/register", {
        "full_name": "Test Student", "email": email, "password": PASSWORD, "confirm_password": PASSWORD})
    check("register student returns 201", status == 201, f"{status} {data}")
    check("verification email written to outbox", code_from_email(email) is not None)

    status, data = student.post("/api/auth/register", {
        "full_name": "Test Student", "email": email, "password": "short", "confirm_password": "short"})
    check("weak password rejected with 422", status == 422)

    status, data = student.post("/api/auth/register", {
        "full_name": "Test Student", "email": email, "password": PASSWORD, "confirm_password": "Different123"})
    check("mismatched passwords rejected with 422", status == 422)

    status, data = student.post("/api/auth/register", {
        "full_name": "Fake", "email": "someone@example.com", "password": PASSWORD, "confirm_password": PASSWORD})
    check("domain without mail server rejected", status == 400, f"{status} {data}")

    status, data = student.post("/api/auth/resend-verification", {"email": email})
    check("resend within 60 seconds is rate limited (429)", status == 429, f"{status} {data}")

    status, data = student.login(email, PASSWORD)
    check("login before verification is blocked (403)",
          status == 403 and isinstance(detail(data), dict) and detail(data).get("code") == "email_not_verified",
          f"{status} {data}")

    status, data = student.get("/api/student/profile")
    check("protected endpoint without login returns 401", status == 401)

    code = code_from_email(email)
    wrong = "000000" if code != "000000" else "111111"
    status, data = student.post("/api/auth/verify-email", {"email": email, "code": wrong})
    check("wrong verification code rejected", status == 400 and "attempt" in str(detail(data)), f"{status} {data}")

    status, data = student.post("/api/auth/verify-email", {"email": email, "code": code})
    check("correct code verifies and logs in", status == 200 and data.get("access_token"), f"{status} {data}")
    student.token = data.get("access_token")
    check("confirmation email sent", "account is ready" in (latest_email(email) or {}).get("subject", "").lower())

    status, data = student.post("/api/auth/verify-email", {"email": email, "code": code})
    check("used code cannot be reused", status == 400)

    status, data = student.post("/api/auth/register", {
        "full_name": "Test Student", "email": email, "password": PASSWORD, "confirm_password": PASSWORD})
    check("duplicate registration of verified email returns 409", status == 409)
    status, data = student.post("/api/auth/register", {
        "full_name": "Test Student", "email": email.upper(), "password": PASSWORD, "confirm_password": PASSWORD})
    check("registering the same email in upper case returns 409 (case-insensitive)", status == 409, f"{status} {data}")

    other = Client()
    status, data = other.login(email, "WrongPass999")
    check("wrong password returns 401", status == 401)
    status, data = other.login(email.upper(), PASSWORD)
    check("login works (email is case-insensitive)", status == 200 and data["user"]["role"] == "student",
          f"{status} {data}")

    status, data = student.get("/api/auth/me")
    check("/me returns the student", status == 200 and data["email"] == email and data["role"] == "student")

    status, data = student.post("/api/auth/refresh")
    check("refresh cookie issues a new access token", status == 200 and data.get("access_token"), f"{status} {data}")
    return student, email


def test_refresh_rotation():
    print("\nRefresh token rotation and logout")
    email = test_email("stu")
    client = Client()
    client.login(email, PASSWORD)
    old_cookie = next(cookie for cookie in client.cookies if cookie.name == "zyntra_refresh")
    old_value = old_cookie.value

    status, _ = client.post("/api/auth/refresh")
    check("first refresh succeeds", status == 200)

    replay = Client()
    req = urllib.request.Request(BASE + "/api/auth/refresh", data=b"{}", method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Cookie", f"zyntra_refresh={old_value}")
    try:
        urllib.request.urlopen(req, timeout=30)
        replay_status = 200
    except urllib.error.HTTPError as error:
        replay_status = error.code
    check("old refresh token cannot be used again (401)", replay_status == 401)

    status, _ = client.post("/api/auth/logout")
    check("logout succeeds", status == 200)
    status, data = client.post("/api/auth/refresh")
    check("refresh after logout gives no session (cookie cleared)", status in (204, 401) and not data)

    status, _ = Client().post("/api/auth/refresh")
    check("refresh without any cookie returns 204 (not an error)", status == 204)


def test_profile(student):
    print("\nStudent profile")
    status, data = student.get("/api/student/profile")
    check("student can read own profile", status == 200 and data["completeness_percent"] == 0, f"{status} {data}")

    full_profile = {
        "full_name": "Test Student Updated", "contact_number": "+92 300 1234567",
        "previous_qualification": "Intermediate (HSSC)", "academic_background": "Pre-Engineering",
        "board_or_university": "Test Board", "passing_year": 2025, "obtained_marks": 780, "total_marks": 1100,
    }
    status, data = student.put("/api/student/profile", full_profile)
    check("student can update own profile", status == 200, f"{status} {data}")
    check("percentage calculated from marks", status == 200 and abs(data["percentage"] - 70.91) < 0.01,
          str(data.get("percentage") if isinstance(data, dict) else data))

    status, data = student.put("/api/student/profile", {"full_name": "X", "previous_qualification": "PhD from Mars"})
    check("invalid profile data rejected (422)", status == 422)

    for label, body in [
        ("percentage above 100", {"percentage": 100.5}),
        ("negative percentage", {"percentage": -1}),
        ("obtained marks above total", {"obtained_marks": 1200, "total_marks": 1100}),
        ("negative obtained marks", {"obtained_marks": -5, "total_marks": 1100}),
    ]:
        status, _ = student.put("/api/student/profile", {"full_name": "Test Student Updated", **body})
        check(f"profile {label} rejected (422)", status == 422, str(status))
    status, data = student.put("/api/student/profile", {"full_name": "Test Student Updated", "percentage": 100})
    check("profile percentage 100 accepted", status == 200 and data["percentage"] == 100, f"{status} {data}")
    student.put("/api/student/profile", full_profile)  # restore the profile used by later checks


def test_student_blocked_from_admin(student):
    print("\nStudents cannot reach admin endpoints")
    for path in ["/api/admin/overview", "/api/admin/users", "/api/admin/scholarships", "/api/admin/invitations"]:
        status, _ = student.get(path)
        check(f"student GET {path} -> 403", status == 403, str(status))
    status, _ = student.post("/api/admin/scholarships", {"title": "Hack attempt"})
    check("student POST /api/admin/scholarships -> 403", status == 403)
    status, _ = student.patch("/api/admin/users/1", {"is_active": False})
    check("student PATCH /api/admin/users/1 -> 403", status == 403)


def test_password_reset(email):
    print("\nForgot password")
    client = Client()
    status, data = client.post("/api/auth/forgot-password", {"email": test_email("nobody")})
    generic = data.get("message") if isinstance(data, dict) else None
    check("unknown email gets the generic response", status == 200)

    # Requested in upper case: the account is still found (emails are case-insensitive)
    status, data = client.post("/api/auth/forgot-password", {"email": email.upper()})
    check("registered email (typed in upper case) gets the same generic response", status == 200 and data.get("message") == generic)
    code = code_from_email(email)
    check("reset code email written", code is not None and "reset" in latest_email(email)["subject"].lower())

    status, _ = client.post("/api/auth/reset-password/verify-code", {"email": email, "code": "999999" if code != "999999" else "888888"})
    check("wrong reset code rejected", status == 400)

    status, data = client.post("/api/auth/reset-password/verify-code", {"email": email.title(), "code": code})
    check("correct reset code (email in mixed case) returns a reset token", status == 200 and data.get("reset_token"), f"{status} {data}")
    reset_token = data.get("reset_token")

    new_password = "NewPass456"
    status, data = client.post("/api/auth/reset-password", {
        "reset_token": reset_token, "password": new_password, "confirm_password": new_password})
    check("password reset succeeds", status == 200, f"{status} {data}")
    check("password-changed email sent", "changed" in latest_email(email)["subject"].lower())

    status, _ = client.post("/api/auth/reset-password", {
        "reset_token": reset_token, "password": "Another789", "confirm_password": "Another789"})
    check("reset token cannot be reused", status == 400)

    status, _ = Client().login(email, PASSWORD)
    check("old password no longer works", status == 401)
    status, _ = Client().login(email, new_password)
    check("new password works", status == 200)

    # Restore the original password for later steps
    db = SessionLocal()
    from app.core.security import hash_password
    user = db.query(User).filter(User.email == email).first()
    user.password_hash = hash_password(PASSWORD)
    db.commit()
    db.close()


def create_test_root():
    db = SessionLocal()
    user = create_root_admin(db, "Test Root Admin", test_email("root"), PASSWORD)
    db.close()
    return user


def test_invitations(root):
    print("\nStaff invitations")
    staff = {}
    plans = {
        "read": {"scholarships": "read"},
        "write": {"scholarships": "write"},
        "rw": {"scholarships": "read_write", "roadmaps": "read_write", "test_prep": "read_write", "programs": "read_write"},
    }
    for label, permissions in plans.items():
        email = test_email(f"staff{label}")
        status, data = root.post("/api/admin/invitations", {
            "full_name": f"Test Staff {label}", "email": email, "permissions": permissions})
        check(f"root creates invitation ({label})", status == 201 and data["status"] == "pending", f"{status} {data}")
        mail = latest_email(email)
        token = re.search(r"token=([A-Za-z0-9_\-]+)", mail["text"]).group(1) if mail else None
        check(f"invitation email contains a link ({label})", token is not None)
        staff[label] = {"email": email, "token": token, "client": Client()}

    status, data = root.post("/api/admin/invitations", {
        "full_name": "Dup", "email": test_email("stu"), "permissions": {"scholarships": "read"}})
    check("cannot invite an email that already has an account (409)", status == 409)

    status, data = root.post("/api/admin/invitations", {"full_name": "None", "email": test_email("x"), "permissions": {}})
    check("invitation without any module rejected (400)", status == 400)

    token = staff["read"]["token"]
    status, data = Client().get(f"/api/invitations/preview?token={token}")
    check("invitation preview shows name and email", status == 200 and data["email"] == staff["read"]["email"])

    status, data = Client().post("/api/invitations/accept", {"token": token, "password": "weak", "confirm_password": "weak"})
    check("weak password rejected on invitation (422)", status == 422)

    for label, item in staff.items():
        status, data = item["client"].post("/api/invitations/accept", {
            "token": item["token"], "password": PASSWORD, "confirm_password": PASSWORD})
        check(f"staff accepts invitation ({label})", status == 200 and data["user"]["role"] == "staff", f"{status} {data}")
        item["client"].token = data.get("access_token")

    status, data = Client().post("/api/invitations/accept", {"token": token, "password": PASSWORD, "confirm_password": PASSWORD})
    check("used invitation link cannot be reused", status == 400 and "already been used" in str(detail(data)))

    # Expired invitation
    expired_email = test_email("expired")
    root.post("/api/admin/invitations", {"full_name": "Expired", "email": expired_email, "permissions": {"roadmaps": "read"}})
    expired_token = re.search(r"token=([A-Za-z0-9_\-]+)", latest_email(expired_email)["text"]).group(1)
    db = SessionLocal()
    inv = db.query(StaffInvitation).filter(StaffInvitation.email == expired_email).first()
    inv.expires_at = utcnow() - timedelta(hours=1)
    db.commit()
    db.close()
    status, data = Client().get(f"/api/invitations/preview?token={expired_token}")
    check("expired invitation rejected", status == 400 and "expired" in str(detail(data)).lower())

    # Revoked invitation
    revoked_email = test_email("revoked")
    status, data = root.post("/api/admin/invitations", {"full_name": "Revoked", "email": revoked_email, "permissions": {"roadmaps": "read"}})
    revoked_token = re.search(r"token=([A-Za-z0-9_\-]+)", latest_email(revoked_email)["text"]).group(1)
    root.delete(f"/api/admin/invitations/{data['id']}")
    status, data = Client().get(f"/api/invitations/preview?token={revoked_token}")
    check("revoked invitation rejected", status == 400)

    status, data = staff["read"]["client"].post("/api/admin/invitations", {
        "full_name": "Sneaky", "email": test_email("sneaky"), "permissions": {"scholarships": "read_write"}})
    check("staff cannot create invitations (403)", status == 403)
    status, data = staff["read"]["client"].get("/api/admin/users")
    check("staff cannot list users (403)", status == 403)
    me_id = staff["read"]["client"].get("/api/auth/me")[1]["id"]
    status, data = staff["read"]["client"].put(f"/api/admin/staff/{me_id}/permissions", {"permissions": {"scholarships": "read_write"}})
    check("staff cannot change their own permissions (403)", status == 403)
    return staff


def scholarship_body(title, status="draft"):
    return {
        "title": title, "scholarship_type": "Test type", "summary": "Test summary",
        "eligibility_criteria": ["Criterion A", "  ", "Criterion B"], "benefits": ["Benefit A"],
        "required_documents": ["Doc A"], "application_steps": [{"title": "Step 1", "description": "Do it"}],
        "conditions": [], "status": status,
    }


def test_permissions_and_scholarships(root, staff, student):
    print("\nModule permissions and scholarship publishing")
    title = f"Test Scholarship {RUN_ID}"
    status, data = root.post("/api/admin/scholarships", scholarship_body(title))
    check("root creates a draft scholarship", status == 201 and data["eligibility_criteria"] == ["Criterion A", "Criterion B"],
          f"{status} {data}")
    root_sch_id = data["id"]

    reader = staff["read"]["client"]
    status, data = reader.get("/api/admin/scholarships")
    check("read staff can list scholarships", status == 200 and any(s["id"] == root_sch_id for s in data))
    check("read staff records have can_edit = false", status == 200 and not any(s["can_edit"] for s in data))
    status, _ = reader.post("/api/admin/scholarships", scholarship_body("Read staff attempt"))
    check("read staff cannot create (403)", status == 403)
    status, _ = reader.put(f"/api/admin/scholarships/{root_sch_id}", scholarship_body("Changed by reader"))
    check("read staff cannot edit via direct API call (403)", status == 403)
    status, _ = reader.delete(f"/api/admin/scholarships/{root_sch_id}")
    check("read staff cannot delete (403)", status == 403)
    status, _ = reader.get("/api/admin/roadmaps")
    check("staff without roadmap access gets 403", status == 403)

    writer = staff["write"]["client"]
    status, data = writer.post("/api/admin/scholarships", scholarship_body(f"Writer Scholarship {RUN_ID}"))
    check("write staff can create", status == 201, f"{status} {data}")
    writer_sch_id = data.get("id")
    status, data = writer.get("/api/admin/scholarships")
    check("write staff only see their own records", status == 200 and [s["id"] for s in data] == [writer_sch_id],
          str(data))
    status, _ = writer.put(f"/api/admin/scholarships/{root_sch_id}", scholarship_body("Changed by writer"))
    check("write staff cannot edit others' records (404)", status == 404)
    status, data = writer.put(f"/api/admin/scholarships/{writer_sch_id}", scholarship_body(f"Writer Scholarship {RUN_ID} v2"))
    check("write staff can edit their own record", status == 200 and data["title"].endswith("v2"))

    editor = staff["rw"]["client"]
    status, data = editor.put(f"/api/admin/scholarships/{root_sch_id}", scholarship_body(title + " edited"))
    check("read+write staff can edit any record", status == 200, f"{status} {data}")

    status, data = student.get("/api/content/scholarships")
    check("draft scholarship hidden from students", status == 200 and not any(s["id"] == root_sch_id for s in data))
    status, _ = student.get(f"/api/content/scholarships/{root_sch_id}")
    check("draft scholarship detail returns 404 for students", status == 404)

    status, data = root.put(f"/api/admin/scholarships/{root_sch_id}", scholarship_body(title + " published", "published"))
    check("root publishes scholarship", status == 200 and data["status"] == "published")
    status, data = student.get(f"/api/content/scholarships/{root_sch_id}")
    check("published scholarship visible to student with latest edit",
          status == 200 and data["title"] == title + " published", f"{status} {data}")

    root.put(f"/api/admin/scholarships/{root_sch_id}", scholarship_body(title + " published", "draft"))
    status, _ = student.get(f"/api/content/scholarships/{root_sch_id}")
    check("unpublished scholarship hidden again", status == 404)

    status, _ = writer.delete(f"/api/admin/scholarships/{writer_sch_id}")
    check("write staff can delete own record", status == 200)

    # Permission change takes effect immediately
    writer_id = writer.get("/api/auth/me")[1]["id"]
    status, data = root.put(f"/api/admin/staff/{writer_id}/permissions", {"permissions": {"scholarships": "read"}})
    check("root changes staff permissions", status == 200 and data["permissions"] == {"scholarships": "read"})
    status, _ = writer.post("/api/admin/scholarships", scholarship_body("After downgrade"))
    check("downgraded staff can no longer create (403)", status == 403)
    return root_sch_id


def test_roadmaps(root, staff, student):
    print("\nRoadmaps: branches, steps and detail sections")
    editor = staff["rw"]["client"]
    reader, writer = staff["read"]["client"], staff["write"]["client"]
    # Give the read and write staff access to roadmaps for these checks
    for label, level in (("read", "read"), ("write", "write")):
        staff_id = staff[label]["client"].get("/api/auth/me")[1]["id"]
        root.put(f"/api/admin/staff/{staff_id}/permissions", {"permissions": {"scholarships": "read", "roadmaps": level}})

    status, data = editor.post("/api/admin/roadmaps", {"title": f"Computer Science {RUN_ID}"})
    check("staff with roadmap write access creates roadmap", status == 201, f"{status} {data}")
    check("roadmap responses no longer contain category or summary", status == 201 and not {"category", "summary"} & set(data))
    roadmap_id = data["id"]

    status, b1 = editor.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Software Development"})
    check("add branch with the default colour", status == 201 and b1["color"] == "#2563EB" and b1["position"] == 0, f"{status} {b1}")
    status, b2 = editor.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Data Science", "color": "#16a34a"})
    check("add second branch with its own colour (stored upper-case)", status == 201 and b2["color"] == "#16A34A" and b2["position"] == 1)
    status, b3 = editor.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Cybersecurity", "color": "#EA580C"})
    check("any number of branches can be added", status == 201 and b3["position"] == 2)
    status, _ = editor.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Bad colour", "color": "blue"})
    check("invalid branch colour rejected (422)", status == 422)

    sections = [
        {"section_title": "Skills", "section_type": "skills", "content": {"items": ["Python basics", " ", "Problem solving"]}},
        {"section_title": "Tools & Technologies", "section_type": "tools", "content": {"items": ["Python", "Git"]}},
        {"section_title": "Projects", "section_type": "list", "content": {"items": ["Build a calculator"]}},
        {"section_title": "Notes", "section_type": "text", "content": {"text": "Take your time."}},
        {"section_title": "Learning Resources", "section_type": "links",
         "content": {"links": [{"label": "Docs", "url": "https://docs.python.org"}]}},
    ]
    status, n1 = editor.post(f"/api/admin/roadmap-branches/{b1['id']}/nodes", {
        "title": "Programming fundamentals", "description": "Start here.", "sections": sections})
    check("add step with skills, tools and custom sections", status == 201 and len(n1["sections"]) == 5, f"{status} {n1}")
    check("section order kept and blank items dropped",
          status == 201 and [x["section_title"] for x in n1["sections"]][:2] == ["Skills", "Tools & Technologies"]
          and n1["sections"][0]["content"] == {"items": ["Python basics", "Problem solving"]}, str(n1.get("sections")))
    status, _ = editor.post(f"/api/admin/roadmap-branches/{b1['id']}/nodes", {
        "title": "Bad", "sections": [{"section_title": "X", "section_type": "video", "content": {}}]})
    check("unknown section type rejected (422)", status == 422)
    status, _ = editor.post(f"/api/admin/roadmap-branches/{b1['id']}/nodes", {
        "title": "Bad link", "sections": [{"section_title": "Links", "section_type": "links",
                                           "content": {"links": [{"label": "x", "url": "javascript:alert(1)"}]}}]})
    check("non-http link in a links section rejected (422)", status == 422)

    status, n2 = editor.post(f"/api/admin/roadmap-branches/{b1['id']}/nodes", {"title": "Web development", "is_default": True})
    check("add second step marked as default", status == 201 and n2["position"] == 1 and n2["is_default"] is True)
    status, n3 = editor.post(f"/api/admin/roadmap-branches/{b2['id']}/nodes", {"title": "Statistics", "is_default": True})
    status, data = editor.get(f"/api/admin/roadmaps/{roadmap_id}")
    defaults = [n["id"] for b in data["branches"] for n in b["nodes"] if n["is_default"]] if status == 200 else []
    check("only one default step per roadmap", defaults == [n3["id"]], str(defaults))

    status, data = editor.put(f"/api/admin/roadmap-branches/{b1['id']}/nodes/order", {"ids": [n2["id"], n1["id"]]})
    check("reorder steps in a branch", status == 200 and [n["id"] for n in data["nodes"]] == [n2["id"], n1["id"]], f"{status} {data}")
    status, _ = editor.put(f"/api/admin/roadmap-branches/{b1['id']}/nodes/order", {"ids": [n2["id"]]})
    check("reorder with a missing step rejected (400)", status == 400)
    status, data = editor.put(f"/api/admin/roadmaps/{roadmap_id}/branches/order", {"ids": [b2["id"], b1["id"], b3["id"]]})
    check("reorder branches", status == 200 and [b["id"] for b in data] == [b2["id"], b1["id"], b3["id"]], f"{status} {data}")

    status, data = editor.put(f"/api/admin/roadmap-nodes/{n1['id']}", {
        "title": "Programming basics", "description": "Updated.", "sections": [sections[1], sections[0]]})
    check("edit step replaces and reorders its sections",
          status == 200 and data["title"] == "Programming basics"
          and [x["section_type"] for x in data["sections"]] == ["tools", "skills"], f"{status} {data}")
    status, data = editor.put(f"/api/admin/roadmap-branches/{b3['id']}", {"name": "Security", "color": "#DC2626"})
    check("edit branch name and colour", status == 200 and data["name"] == "Security" and data["color"] == "#DC2626")

    status, _ = student.get(f"/api/content/roadmaps/{roadmap_id}")
    check("draft roadmap hidden from student", status == 404)
    editor.put(f"/api/admin/roadmaps/{roadmap_id}", {"title": f"Computer Science {RUN_ID}", "status": "published"})
    status, data = student.get(f"/api/content/roadmaps/{roadmap_id}")
    ok = status == 200 and [b["name"] for b in data["branches"]] == ["Data Science", "Software Development", "Security"]
    check("published roadmap shows branches in order with colours", ok and data["branches"][2]["color"] == "#DC2626", f"{status} {data}")
    check("student sees steps in order with their sections",
          ok and [n["title"] for n in data["branches"][1]["nodes"]] == ["Web development", "Programming basics"]
          and data["branches"][1]["nodes"][1]["sections"][0]["content"] == {"items": ["Python", "Git"]})
    check("student list shows branch and step counts",
          any(r["id"] == roadmap_id and r["branch_count"] == 3 and r["node_count"] == 3 for r in student.get("/api/content/roadmaps")[1]))

    status, _ = student.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Student branch"})
    check("student cannot add branches (403)", status == 403)
    status, data = reader.get(f"/api/admin/roadmaps/{roadmap_id}")
    check("read-only staff can view the roadmap structure", status == 200 and data["can_edit"] is False and len(data["branches"]) == 3)
    status, _ = reader.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Read-only branch"})
    check("read-only staff cannot add branches (403)", status == 403)
    status, _ = reader.put(f"/api/admin/roadmap-nodes/{n1['id']}", {"title": "Changed"})
    check("read-only staff cannot edit steps (403)", status == 403)
    status, _ = writer.post(f"/api/admin/roadmaps/{roadmap_id}/branches", {"name": "Not mine"})
    check("write staff cannot change someone else's roadmap (404)", status == 404)
    status, own = writer.post("/api/admin/roadmaps", {"title": f"Writer Roadmap {RUN_ID}"})
    status, own_branch = writer.post(f"/api/admin/roadmaps/{own['id']}/branches", {"name": "My branch"})
    check("write staff can build their own roadmap", status == 201, f"{status} {own_branch}")

    status, _ = editor.delete(f"/api/admin/roadmap-nodes/{n2['id']}")
    check("delete a step", status == 200)
    status, _ = editor.delete(f"/api/admin/roadmap-branches/{b1['id']}")
    status, data = student.get(f"/api/content/roadmaps/{roadmap_id}")
    check("deleting a branch removes it and its steps",
          status == 200 and [b["name"] for b in data["branches"]] == ["Data Science", "Security"], f"{status} {data}")
    status, data = root.get("/api/admin/roadmaps")
    check("admin list shows branch counts", status == 200 and any(r["id"] == roadmap_id and r["branch_count"] == 2 for r in data))
    status, data = Client().get("/api/public/form-options")
    check("form options list section types and branch colours",
          status == 200 and "skills" in data["roadmap_section_types"] and len(data["roadmap_branch_colors"]) == 6)


def test_test_prep(editor, student):
    print("\nTest preparation (learning content only, no quizzes)")
    status, subject = editor.post("/api/admin/test-prep/subjects", {"name": f"Test Subject {RUN_ID}", "status": "published"})
    check("create subject", status == 201 and "question_count" not in subject, f"{status} {subject}")
    sid = subject["id"]
    status, topic = editor.post(f"/api/admin/test-prep/subjects/{sid}/topics", {
        "title": "Test Topic", "explanation": "Explained", "status": "published"})
    check("create topic", status == 201)
    tid = topic["id"]
    status, draft_topic = editor.post(f"/api/admin/test-prep/subjects/{sid}/topics", {"title": "Draft Topic", "status": "draft"})
    check("create draft topic", status == 201)
    status, data = editor.post(f"/api/admin/test-prep/subjects/{sid}/topics", {"title": "Test Topic"})
    check("duplicate topic title in the same subject rejected (409)", status == 409, f"{status} {data}")
    status, data = editor.put(f"/api/admin/test-prep/topics/{draft_topic['id']}", {"title": "Test Topic", "status": "draft"})
    check("renaming a topic to an existing title rejected (409)", status == 409, f"{status} {data}")
    status, other_subject = editor.post("/api/admin/test-prep/subjects", {"name": f"Test Subject B {RUN_ID}"})
    status, _ = editor.post(f"/api/admin/test-prep/subjects/{other_subject['id']}/topics", {"title": "Test Topic"})
    check("same topic title under a different subject accepted", status == 201, str(status))
    status, _ = editor.post(f"/api/admin/test-prep/subjects/{sid}/resources", {
        "title": "Test video", "url": "https://www.youtube.com/watch?v=test", "resource_type": "video", "topic_id": tid})
    check("add learning resource", status == 201)
    status, _ = editor.post(f"/api/admin/test-prep/subjects/{sid}/resources", {
        "title": "Past paper 2025", "url": "https://example.org/paper.pdf", "resource_type": "pdf"})
    check("add past paper (type pdf)", status == 201)
    statuses = [editor.post(f"/api/admin/test-prep/subjects/{sid}/resources", {
        "title": "Old type", "url": "https://example.org", "resource_type": kind})[0] for kind in ("past_paper", "platform", "podcast")]
    check("resource types outside video/article/pdf/link rejected (422)", statuses == [422, 422, 422], str(statuses))
    status, data = editor.post(f"/api/admin/test-prep/subjects/{sid}/resources", {
        "title": "Khan Academy", "url": "https://www.khanacademy.org"})
    check("resource type defaults to link", status == 201 and data["resource_type"] == "link", f"{status} {data}")

    status, data = editor.get(f"/api/admin/test-prep/subjects/{sid}")
    check("admin subject detail counts topics and resources",
          status == 200 and data["topic_count"] == 2 and data["resource_count"] == 3, f"{status} {data}")
    status, data = editor.get(f"/api/admin/test-prep/topics/{tid}")
    check("admin topic detail has no questions", status == 200 and "questions" not in data, f"{status} {data}")

    status, data = student.get(f"/api/content/test-prep/subjects/{sid}")
    check("student sees published topics only",
          status == 200 and [t["title"] for t in data["topics"]] == ["Test Topic"], f"{status} {data}")
    check("student sees subject resources and past papers", status == 200 and len(data["resources"]) == 3)
    status, data = student.get(f"/api/content/test-prep/topics/{tid}")
    check("student topic shows explanation and resources",
          status == 200 and data["explanation"] == "Explained" and len(data["resources"]) == 1, f"{status} {data}")
    check("student topic has no quiz questions", status == 200 and "questions" not in data)
    status, _ = student.get(f"/api/content/test-prep/topics/{draft_topic['id']}")
    check("draft topic hidden from student", status == 404)

    removed = [
        (student, "POST", "/api/student/practice/answer", {"question_id": 1, "option_id": 1}),
        (student, "GET", "/api/student/practice/stats", None),
        (student, "POST", "/api/student/mock-tests", {"subject_id": sid}),
        (student, "POST", "/api/student/mock-tests/submit", {"answers": []}),
        (editor, "POST", f"/api/admin/test-prep/topics/{tid}/questions", {"question_text": "x", "options": []}),
        (editor, "PUT", "/api/admin/test-prep/questions/1", {"question_text": "x", "options": []}),
    ]
    statuses = [client.request(method, path, body)[0] for client, method, path, body in removed]
    check("practice question and mock test endpoints are removed (404)", statuses == [404] * len(removed), str(statuses))
    status, data = Client().get("/api/public/form-options")
    check("form options no longer list question difficulties", status == 200 and "question_difficulties" not in data)


def test_programs_and_eligibility(editor, student):
    print("\nPrograms and preliminary eligibility")
    status, program = editor.post("/api/admin/programs", {
        "name": f"Test Program {RUN_ID}", "min_percentage": 60, "accepted_qualifications": ["Intermediate (HSSC)"],
        "status": "published"})
    check("create program with eligibility criteria", status == 201 and program["slug"], f"{status} {program}")

    status, data = Client().get(f"/api/public/programs/{program['slug']}")
    check("published program visible on public page", status == 200)
    statuses = [editor.post("/api/admin/programs", {"name": f"Bad Program {RUN_ID}", "min_percentage": v})[0] for v in (-1, 101)]
    check("program minimum percentage outside 0-100 rejected (422)", statuses == [422, 422], str(statuses))

    status, data = student.get("/api/student/eligibility")
    entry = next((p for p in data.get("programs", []) if p["program_id"] == program["id"]), None) if status == 200 else None
    check("eligibility: student meets listed criteria", entry is not None and entry["status"] == "meets_listed_criteria",
          str(entry))
    check("eligibility response includes the disclaimer", status == 200 and "not an official admission decision" in data["disclaimer"])

    editor.put(f"/api/admin/programs/{program['id']}", {
        "name": f"Test Program {RUN_ID}", "min_percentage": 85, "accepted_qualifications": ["Intermediate (HSSC)"],
        "status": "published"})
    status, data = student.get("/api/student/eligibility")
    entry = next((p for p in data["programs"] if p["program_id"] == program["id"]), None)
    check("eligibility: below raised minimum shows not_met", entry is not None and entry["status"] == "not_met", str(entry))

    status, _ = editor.put(f"/api/admin/programs/{program['id']}", {"name": f"Test Program {RUN_ID}", "status": "draft"})
    status, _ = Client().get(f"/api/public/programs/{program['slug']}")
    check("draft program hidden from public", status == 404)


def program_body(program, **changes):
    """The full edit form of a program as the dashboard sends it, with some fields changed."""
    fields = ("name", "department", "degree_level", "duration", "summary", "description", "admission_requirements",
              "min_percentage", "accepted_qualifications", "eligibility_notes", "status", "sort_order")
    return {**{field: program[field] for field in fields}, **changes}


def test_program_editing(root):
    print("\nProgram editing (records inserted directly in the database) and display order")
    from sqlalchemy import text
    name = f"Legacy Program t{RUN_ID}"
    legacy_qualifications = ["Intermediate (HSSC)", "12th Grade", "Bachelor\\u0027s degree (16 years)"]
    db = SessionLocal()
    try:
        # Inserted the way the 8 programs were added in Neon: plain SQL, no creator, non-standard qualifications
        program_id = db.execute(text(
            "INSERT INTO programs (name, slug, department, summary, min_percentage, accepted_qualifications, status, sort_order) "
            "VALUES (:name, :slug, 'Test Department', 'Original summary', 50, CAST(:quals AS jsonb), 'draft', 99) RETURNING id"
        ), {"name": name, "slug": f"legacy-program-t{RUN_ID}", "quals": json.dumps(legacy_qualifications)}).scalar()
        db.commit()
        other = db.query(Program).filter(Program.id != program_id).order_by(Program.id).first()
        other_id, other_before = (other.id, (other.updated_at, other.summary)) if other else (None, None)
    finally:
        db.close()

    status, programs = root.get("/api/admin/programs")
    record = next((p for p in programs if p["id"] == program_id), None) if status == 200 else None
    check("SQL-inserted program is listed and editable", record is not None and record["can_edit"], str(record))

    status, data = root.put(f"/api/admin/programs/{program_id}", program_body(record, summary=f"Edited summary {RUN_ID}"))
    check("SQL-inserted program with non-standard qualifications can be updated", status == 200, f"{status} {data}")
    db = SessionLocal()
    try:
        saved = db.get(Program, program_id)
        check("update is stored in the database", saved.summary == f"Edited summary {RUN_ID}")
        check("existing qualifications and other fields are kept",
              saved.accepted_qualifications == legacy_qualifications and saved.department == "Test Department"
              and float(saved.min_percentage) == 50 and saved.sort_order == 99 and saved.name == name,
              f"{saved.accepted_qualifications} {saved.department} {saved.min_percentage} {saved.sort_order}")
        if other_before:
            other = db.get(Program, other_id)
            check("editing one program does not change another", (other.updated_at, other.summary) == other_before)
    finally:
        db.close()

    status, data = root.put(f"/api/admin/programs/{program_id}",
                            program_body(record, accepted_qualifications=["Intermediate (HSSC)", "Made-up qualification"]))
    check("a new non-standard qualification is rejected (422)", status == 422 and "Made-up qualification" in str(data), f"{status}")
    status, data = root.put(f"/api/admin/programs/{program_id}",
                            program_body(record, accepted_qualifications=["Intermediate (HSSC)", "A-Levels"]))
    check("an existing qualification can be removed and a standard one added",
          status == 200 and data["accepted_qualifications"] == ["Intermediate (HSSC)", "A-Levels"], f"{status}")
    record = data if status == 200 else record
    status, data = root.post("/api/admin/programs", {"name": f"Bad Quals t{RUN_ID}", "accepted_qualifications": ["12th Grade"]})
    check("a new program cannot use a non-standard qualification (422)", status == 422, str(status))

    cases = {1: 200, 100: 200, 50: 200, 0: 422, -1: 422, -100: 422, 101: 422, 1.5: 422, None: 422, "": 422, "abc": 422, "7": 422}
    outcome = {repr(value): root.put(f"/api/admin/programs/{program_id}", program_body(record, sort_order=value))[0]
               for value in cases}
    expected = {repr(value): code for value, code in cases.items()}
    check("display order: 1, 50 and 100 accepted; 0, negatives, 101, 1.5, empty, text and numbers sent as text rejected",
          outcome == expected, str(outcome))
    status, _ = root.put(f"/api/admin/programs/{program_id}", program_body(record, sort_order=True))
    check("display order true/false rejected (422)", status == 422, str(status))
    status, _ = root.put(f"/api/admin/programs/{program_id}", program_body(record, sort_order=50))
    status, data = root.put(f"/api/admin/programs/{program_id}", program_body(record, sort_order=-5))
    check("display order error message is clear", status == 422 and "whole number from 1 to 100" in str(data), str(data))

    db = SessionLocal()
    try:
        for value in (0, 101):
            try:
                db.execute(text("UPDATE programs SET sort_order = :v WHERE id = :id"), {"v": value, "id": program_id})
                db.commit()
                rejected = False
            except Exception as error:  # noqa: BLE001 - the CHECK constraint violation is what is being tested
                db.rollback()
                rejected = "ck_programs_sort_order_range" in str(error)
            check(f"database CHECK rejects display order {value}", rejected)
        check("last accepted display order (50) is stored", db.get(Program, program_id).sort_order == 50)
    finally:
        db.close()

    status, created = root.post("/api/admin/programs", {"name": f"New Program t{RUN_ID}", "status": "draft"})
    check("creating a program without a display order uses 1", status == 201 and created["sort_order"] == 1, f"{status}")
    status, _ = root.delete(f"/api/admin/programs/{created['id']}") if status == 201 else (None, None)
    check("program deletion still works", status == 200)
    status, _ = root.delete(f"/api/admin/programs/{program_id}")
    check("SQL-inserted program can be deleted", status == 200)


ORDER_CASES = {1: 200, 100: 200, 50: 200, 0: 422, -1: 422, -100: 422, 101: 422, 1.5: 422, None: 422, "": 422}


def test_display_order_all_forms(root):
    """Scholarships, test subjects, topics and learning resources: the same 1-100 display order rule."""
    print("\nDisplay order 1-100 on scholarships, test subjects, topics and resources")
    from sqlalchemy import text
    _, scholarship = root.post("/api/admin/scholarships", {"title": f"Order Scholarship {RUN_ID}"})
    _, subject = root.post("/api/admin/test-prep/subjects", {"name": f"Order Subject {RUN_ID}"})
    _, topic = root.post(f"/api/admin/test-prep/subjects/{subject['id']}/topics", {"title": "Order Topic"})
    _, resource = root.post(f"/api/admin/test-prep/subjects/{subject['id']}/resources", {
        "title": "Order Resource", "url": "https://example.org"})
    check("new records without a display order get 1",
          [scholarship.get("sort_order"), subject.get("sort_order"), topic.get("sort_order"), resource.get("sort_order")] == [1, 1, 1, 1])
    forms = {
        "scholarship": (f"/api/admin/scholarships/{scholarship['id']}", {"title": f"Order Scholarship {RUN_ID}"}, "scholarships", scholarship["id"]),
        "test subject": (f"/api/admin/test-prep/subjects/{subject['id']}", {"name": f"Order Subject {RUN_ID}"}, "test_subjects", subject["id"]),
        "topic": (f"/api/admin/test-prep/topics/{topic['id']}", {"title": "Order Topic"}, "test_topics", topic["id"]),
        "learning resource": (f"/api/admin/test-prep/resources/{resource['id']}", {"title": "Order Resource", "url": "https://example.org"},
                              "learning_resources", resource["id"]),
    }
    for label, (path, body, table, record_id) in forms.items():
        outcome = {repr(value): root.put(path, {**body, "sort_order": value})[0] for value in ORDER_CASES}
        expected = {repr(value): code for value, code in ORDER_CASES.items()}
        check(f"{label}: API accepts 1, 50, 100 and rejects 0, -1, -100, 101, 1.5 and empty", outcome == expected, str(outcome))
        db = SessionLocal()
        try:
            rejected = []
            for value in (0, 101):
                try:
                    db.execute(text(f"UPDATE {table} SET sort_order = :v WHERE id = :id"), {"v": value, "id": record_id})
                    db.commit()
                except Exception as error:  # noqa: BLE001 - the CHECK constraint violation is what is being tested
                    db.rollback()
                    rejected.append(f"ck_{table}_sort_order_range" in str(error))
            check(f"{label}: database CHECK rejects 0 and 101", rejected == [True, True], str(rejected))
        finally:
            db.close()
    root.delete(f"/api/admin/scholarships/{scholarship['id']}")
    root.delete(f"/api/admin/test-prep/subjects/{subject['id']}")


def test_contact_phone(root):
    print("\nWebsite contact phone (number only)")
    from sqlalchemy import text
    status, blocks = root.get("/api/admin/site-content")
    block = next(b for b in blocks if b["key"] == "contact_phone")
    original = block["body"]
    base = {"title": block["title"], "status": block["status"]}
    try:
        for value in ("03001234567", "+923001234567", "0092300123456"):
            status, data = root.put(f"/api/admin/site-content/{block['id']}", {**base, "body": value})
            check(f"phone {value!r} accepted and stored exactly (leading zeros and + kept)",
                  status == 200 and data["body"] == value, f"{status} {data}")
        for value in ("0300-1234567", "0300 1234567", "Call 03001234567", "phone", "", "12345", "+92300123456789012", "++923001234567"):
            status, _ = root.put(f"/api/admin/site-content/{block['id']}", {**base, "body": value})
            check(f"phone {value!r} rejected (422)", status == 422, str(status))
        db = SessionLocal()
        try:
            try:
                db.execute(text("UPDATE site_content SET body = 'Call us' WHERE key = 'contact_phone'"))
                db.commit()
                rejected = False
            except Exception as error:  # noqa: BLE001 - the CHECK constraint violation is what is being tested
                db.rollback()
                rejected = "ck_site_content_contact_phone" in str(error)
            check("database CHECK rejects text in the contact phone", rejected)
        finally:
            db.close()
        status, data = root.put(f"/api/admin/site-content/{next(b for b in blocks if b['key'] == 'contact_email')['id']}",
                                {**base, "title": "Email", "body": next(b for b in blocks if b["key"] == "contact_email")["body"]})
        check("other website content (email) is not limited to digits", status == 200, str(status))
    finally:
        db = SessionLocal()
        try:
            db.execute(text("UPDATE site_content SET body = :b WHERE key = 'contact_phone'"), {"b": original})
            db.commit()
        finally:
            db.close()


def test_site_content(root):
    print("\nWebsite content (edit only)")
    status, blocks = root.get("/api/admin/site-content")
    keys = [b["key"] for b in blocks] if status == 200 else []
    check("website content list loads", status == 200 and len(blocks) > 0, f"{status}")
    check("removed sections are not listed", "contact_address" not in keys and "szabist_programs_overview" not in keys, str(keys))
    status, _ = root.post("/api/admin/site-content", {"key": "test_key", "title": "New", "body": "x"})
    check("adding website content is not possible (405)", status == 405, str(status))
    block = next(b for b in blocks if b["key"] == "why_zyntra")
    status, _ = root.delete(f"/api/admin/site-content/{block['id']}")
    check("deleting website content is not possible (405)", status == 405, str(status))

    original = {"title": block["title"], "body": block["body"], "status": block["status"]}
    edited = {"title": block["title"], "body": block["body"] + f" [test {RUN_ID}]", "status": "published", "key": "contact_email"}
    status, data = root.put(f"/api/admin/site-content/{block['id']}", edited)
    check("editing website content works and the section key cannot change",
          status == 200 and data["body"].endswith(f"[test {RUN_ID}]") and data["key"] == "why_zyntra", f"{status} {data}")
    status, public = Client().get("/api/public/site-content")
    check("edited text is shown on the public site", status == 200 and public["why_zyntra"]["body"].endswith(f"[test {RUN_ID}]"))
    status, _ = root.put(f"/api/admin/site-content/{block['id']}", original)
    check("original text restored", status == 200)
    status, options = Client().get("/api/public/form-options")
    check("form options no longer list the removed sections",
          status == 200 and not {"contact_address", "szabist_programs_overview"} & set(options["site_content_keys"]))


def test_root_management(root, staff):
    print("\nRoot admin: overview, users and account control")
    status, data = root.get("/api/admin/overview")
    check("root overview returns database counts",
          status == 200 and data["stats"]["students"] >= 1 and data["stats"]["staff"] >= 3, f"{status} {data}")

    status, data = root.get(f"/api/admin/users?search=t{RUN_ID}&role=staff")
    check("search and role filter", status == 200 and data["total"] == 3, f"{status} {data}")
    status, data = root.get(f"/api/admin/users?search=t{RUN_ID}stu")
    check("view user list item for student", status == 200 and data["total"] == 1)
    student_id = data["items"][0]["id"]
    status, data = root.get(f"/api/admin/users/{student_id}")
    check("view student detail with profile", status == 200 and data["profile"]["previous_qualification"] == "Intermediate (HSSC)")

    reader = staff["read"]["client"]
    reader_id = reader.get("/api/auth/me")[1]["id"]
    status, data = root.patch(f"/api/admin/users/{reader_id}", {"is_active": False})
    check("root deactivates a staff account", status == 200 and data["is_active"] is False)
    status, _ = reader.get("/api/admin/scholarships")
    check("deactivated staff is locked out immediately (401)", status == 401)
    status, _ = reader.post("/api/auth/refresh")
    check("deactivated staff cannot refresh session", status == 401)
    status, _ = Client().login(staff["read"]["email"], PASSWORD)
    check("deactivated staff cannot log in (403)", status == 403)
    root.patch(f"/api/admin/users/{reader_id}", {"is_active": True})
    status, _ = Client().login(staff["read"]["email"], PASSWORD)
    check("reactivated staff can log in", status == 200)

    root_id = root.get("/api/auth/me")[1]["id"]
    status, _ = root.delete(f"/api/admin/users/{root_id}")
    check("root admin accounts cannot be deleted from the dashboard", status == 400)

    status, data = root.get("/api/admin/audit-logs?limit=200")
    actions = {log["action"] for log in data} if status == 200 else set()
    check("audit log records account and content actions",
          {"staff.invited", "invitation.accepted", "scholarship.created", "user.deactivated"} <= actions, str(actions))


def cleanup(run_started):
    print("\nCleaning up test data")
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.email.like(f"zyntra.szabist+t{RUN_ID}%")).all()
        user_ids = [user.id for user in users]
        marker = f"%{RUN_ID}%"
        db.query(Scholarship).filter(Scholarship.title.like(marker)).delete(synchronize_session=False)
        db.query(Roadmap).filter(Roadmap.title.like(marker)).delete(synchronize_session=False)
        db.query(TestSubject).filter(TestSubject.name.like(marker)).delete(synchronize_session=False)
        db.query(Program).filter(Program.name.like(marker)).delete(synchronize_session=False)
        db.query(StaffInvitation).filter(StaffInvitation.email.like(f"zyntra.szabist+t{RUN_ID}%")).delete(synchronize_session=False)
        if user_ids:
            db.query(AuditLog).filter(AuditLog.actor_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.created_at >= run_started, AuditLog.summary.like(f"%t{RUN_ID}%")).delete(synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.created_at >= run_started, AuditLog.summary.like(marker)).delete(synchronize_session=False)
        for user in users:
            db.delete(user)
        db.commit()
        remaining = db.query(User).filter(User.email.like(f"zyntra.szabist+t{RUN_ID}%")).count()
        print(f"  removed {len(users)} test users; remaining test users: {remaining}")
    finally:
        db.close()
    for file in OUTBOX.glob(f"*t{RUN_ID}*"):
        file.unlink()


def main():
    print(f"ZYNTRA API tests (run id {RUN_ID})")
    run_started = utcnow()
    server = start_server()
    try:
        student, student_email = test_student_auth()
        test_refresh_rotation()
        test_profile(student)
        test_student_blocked_from_admin(student)
        test_password_reset(student_email)
        student = Client()
        student.login(student_email, PASSWORD)

        create_test_root()
        root = Client()
        status, _ = root.login(test_email("root"), PASSWORD)
        check("temporary test root admin can log in", status == 200)

        staff = test_invitations(root)
        test_permissions_and_scholarships(root, staff, student)
        test_roadmaps(root, staff, student)
        test_test_prep(staff["rw"]["client"], student)
        test_programs_and_eligibility(staff["rw"]["client"], student)
        test_program_editing(root)
        test_display_order_all_forms(root)
        test_contact_phone(root)
        test_site_content(root)
        test_root_management(root, staff)
    finally:
        server.terminate()
        server.wait(timeout=10)
        cleanup(run_started)

    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed}/{len(results)} checks passed")
    failed = [name for name, ok in results if not ok]
    if failed:
        print("Failed checks:")
        for name in failed:
            print(f"  - {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
