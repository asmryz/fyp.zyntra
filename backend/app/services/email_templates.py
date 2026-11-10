"""
HTML email templates.

Email clients ignore most CSS, so styles are written inline and the layout
uses tables (bgcolor attributes are repeated for Outlook). Every template
returns (subject, html_body, text_body).

Colours are the ones used by the website themes
(frontend/src/styles/public-theme.css and student-theme.css): a coral
background with all text on ink (dark) surfaces. Keeping text off the coral
and aqua areas means it stays readable when mail apps such as Gmail's
dark mode switch dark text to light.
"""
from html import escape

AQUA = "#19E8C9"        # --aqua: page background, greeting, links on ink
CORAL = "#FF4B3E"       # --coral: buttons and accents
INK = "#0E0E0E"         # --ink: the card
INK_RAISED = "#1C1C1C"  # --ink-raised: boxes inside the card
PAPER = "#F4F4EF"       # --paper: text on ink
BLACK = "#0B0B0B"       # --black: text on aqua and coral
TEXT_2 = "#D9D9D2"      # secondary text on ink
MUTED = "#B9B9B2"       # muted text on ink

FONT = "Segoe UI,Helvetica,Arial,sans-serif"


def _layout(preheader, greeting, paragraphs, highlight_html="", security_note=""):
    paragraph_html = "".join(
        f'<p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:{PAPER};">{p}</p>' for p in paragraphs
    )
    security_html = ""
    if security_note:
        security_html = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0 0;">'
            f'<tr><td bgcolor="{INK_RAISED}" style="background:{INK_RAISED};border-left:4px solid {CORAL};'
            f'border-radius:10px;padding:14px 16px;font-size:13px;line-height:1.55;color:{TEXT_2};">'
            f'{security_note}</td></tr></table>'
        )

    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{CORAL};font-family:{FONT};" bgcolor="{CORAL}">
<span style="display:none;max-height:0;overflow:hidden;">{escape(preheader)}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{CORAL}" style="background:{CORAL};padding:32px 12px;">
  <tr><td align="center">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
      <tr><td bgcolor="{INK}" style="background:{INK};border-radius:24px;padding:28px 30px 34px;">
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 24px;"><tr>
          <td width="40" valign="middle" style="width:40px;">
            <div style="width:40px;height:40px;line-height:40px;text-align:center;background:{INK_RAISED};border-radius:20px;
                        font-size:20px;font-weight:800;color:{AQUA};">Z</div>
          </td>
          <td width="12" style="width:12px;"></td>
          <td valign="middle">
            <span style="display:block;font-size:20px;font-weight:800;letter-spacing:4px;line-height:1.1;color:{PAPER};">ZYNTRA</span>
            <span style="display:block;font-size:12px;font-weight:600;color:{MUTED};">SZABIST Admission Assistance</span>
          </td>
        </tr></table>
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 18px;"><tr>
          <td width="44" height="4" bgcolor="{CORAL}" style="width:44px;height:4px;background:{CORAL};font-size:0;line-height:0;">&nbsp;</td>
        </tr></table>
        <p style="margin:0 0 18px;font-size:22px;font-weight:800;line-height:1.25;color:{AQUA};">{greeting}</p>
        {paragraph_html}
        {highlight_html}
        {security_html}
      </td></tr>
      <tr><td height="14" style="height:14px;font-size:0;line-height:0;">&nbsp;</td></tr>
      <tr><td bgcolor="{INK}" style="background:{INK};border-radius:18px;padding:16px 22px;font-size:12px;line-height:1.6;color:{MUTED};">
        This is an automated message from ZYNTRA, an AI-powered admission assistance project for prospective
        SZABIST students. ZYNTRA provides guidance only and does not make official admission decisions.
        Please do not reply to this email.
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def _code_box(code):
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 20px;">'
        f'<tr><td align="center" bgcolor="{INK_RAISED}" style="background:{INK_RAISED};border:2px solid {AQUA};'
        f'border-radius:16px;padding:20px;">'
        f'<span style="font-size:34px;font-weight:800;letter-spacing:10px;color:{AQUA};'
        f'font-family:Consolas,Menlo,monospace;">{escape(code)}</span></td></tr></table>'
    )


def _button(label, url):
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 20px;"><tr>'
        f'<td bgcolor="{CORAL}" style="background:{CORAL};border-radius:999px;">'
        f'<a href="{escape(url)}" style="display:inline-block;padding:14px 26px;font-size:14px;font-weight:800;'
        f'letter-spacing:1px;text-transform:uppercase;text-decoration:none;color:{BLACK};">{escape(label)}</a>'
        f'</td></tr></table>'
        f'<p style="margin:0 0 16px;font-size:12px;line-height:1.5;color:{MUTED};">'
        f'If the button does not work, copy this link into your browser:<br>'
        f'<a href="{escape(url)}" style="color:{AQUA};word-break:break-all;">{escape(url)}</a></p>'
    )


def verification_email(name, code, minutes):
    subject = "Your ZYNTRA verification code"
    html = _layout(
        preheader=f"Your verification code is {code}",
        greeting=f"Hello {escape(name)},",
        paragraphs=["Thank you for creating a ZYNTRA student account. Enter this code to verify your email address:"],
        highlight_html=_code_box(code) + f'<p style="margin:0;font-size:14px;color:{MUTED};">'
                                         f'The code expires in {minutes} minutes and can only be used once.</p>',
        security_note="If you did not create a ZYNTRA account, you can ignore this email. "
                      "Never share this code with anyone.",
    )
    text = (
        f"Hello {name},\n\nYour ZYNTRA verification code is: {code}\n"
        f"It expires in {minutes} minutes and can only be used once.\n\n"
        "If you did not create a ZYNTRA account, ignore this email."
    )
    return subject, html, text


def registration_confirmed_email(name, login_url):
    subject = "Welcome to ZYNTRA - your account is ready"
    html = _layout(
        preheader="Your ZYNTRA student account has been verified.",
        greeting=f"Welcome, {escape(name)}!",
        paragraphs=[
            "Your email address has been verified and your ZYNTRA student account is now active.",
            "You can complete your academic profile, explore programs and roadmaps, review scholarship "
            "information and practise for the admission test.",
        ],
        highlight_html=_button("Go to ZYNTRA", login_url),
        security_note="If you did not create this account, please contact the ZYNTRA team.",
    )
    text = f"Welcome, {name}!\n\nYour ZYNTRA student account is now active.\nLog in: {login_url}"
    return subject, html, text


def password_reset_email(name, code, minutes):
    subject = "Your ZYNTRA password reset code"
    html = _layout(
        preheader=f"Your password reset code is {code}",
        greeting=f"Hello {escape(name)},",
        paragraphs=["We received a request to reset the password for your ZYNTRA account. Use this code:"],
        highlight_html=_code_box(code) + f'<p style="margin:0;font-size:14px;color:{MUTED};">'
                                         f'The code expires in {minutes} minutes and can only be used once.</p>',
        security_note="If you did not request a password reset, ignore this email. "
                      "Your password will not change unless this code is used.",
    )
    text = (
        f"Hello {name},\n\nYour ZYNTRA password reset code is: {code}\n"
        f"It expires in {minutes} minutes.\n\nIf you did not request this, ignore this email."
    )
    return subject, html, text


def password_changed_email(name, changed_at_text):
    subject = "Your ZYNTRA password was changed"
    html = _layout(
        preheader="Your ZYNTRA password was changed.",
        greeting=f"Hello {escape(name)},",
        paragraphs=[
            f"The password for your ZYNTRA account was changed on {escape(changed_at_text)}.",
            "For your security, you have been signed out of all devices. Log in again with your new password.",
        ],
        security_note="If you did not make this change, reset your password immediately "
                      "and contact the ZYNTRA team.",
    )
    text = (
        f"Hello {name},\n\nYour ZYNTRA password was changed on {changed_at_text}.\n"
        "If you did not make this change, reset your password immediately."
    )
    return subject, html, text


def staff_invitation_email(name, inviter_name, accept_url, hours, modules_text):
    subject = "You have been invited to join the ZYNTRA staff team"
    html = _layout(
        preheader="Accept your ZYNTRA staff invitation.",
        greeting=f"Hello {escape(name)},",
        paragraphs=[
            f"{escape(inviter_name)} has invited you to manage content on ZYNTRA as a staff member.",
            f"<strong>Your access:</strong> {escape(modules_text)}",
            "Open the link below to set your password and activate your account.",
        ],
        highlight_html=_button("Accept invitation", accept_url)
        + f'<p style="margin:0;font-size:14px;color:{MUTED};">This invitation expires in {hours} hours '
          "and can only be used once.</p>",
        security_note="If you were not expecting this invitation, ignore this email. "
                      "No account is created unless the invitation is accepted.",
    )
    text = (
        f"Hello {name},\n\n{inviter_name} has invited you to join ZYNTRA as a staff member.\n"
        f"Your access: {modules_text}\n\nAccept the invitation (expires in {hours} hours):\n{accept_url}"
    )
    return subject, html, text


def staff_welcome_email(name, login_url):
    subject = "Your ZYNTRA staff account is active"
    html = _layout(
        preheader="Your ZYNTRA staff account is active.",
        greeting=f"Hello {escape(name)},",
        paragraphs=["Your staff account has been activated. You can now log in to the ZYNTRA staff dashboard."],
        highlight_html=_button("Log in to ZYNTRA", login_url),
        security_note="If you did not accept this invitation, contact the ZYNTRA administrator immediately.",
    )
    text = f"Hello {name},\n\nYour ZYNTRA staff account is active. Log in: {login_url}"
    return subject, html, text
