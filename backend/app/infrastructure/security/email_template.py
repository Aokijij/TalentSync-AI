"""Escaped, self-contained transactional email shared by Resend and SMTP."""
import re
from html import escape
from urllib.parse import parse_qs, urlsplit


def _action(body, public_app_url):
    """Only turn this installation's account/invitation links into a button."""
    base = urlsplit(public_app_url or "")
    if base.scheme not in {"http", "https"} or not base.netloc or base.username or base.password:
        return None
    for candidate in re.findall(r"https?://[^\s<>\"']+", body):
        try:
            parsed = urlsplit(candidate)
            same_origin = (parsed.scheme, parsed.hostname, parsed.port) == (base.scheme, base.hostname, base.port)
        except ValueError:
            continue
        if not same_origin or parsed.username or parsed.password or parsed.fragment:
            continue
        query = parse_qs(parsed.query)
        if len(query.get("token", [])) != 1 or not query["token"][0]:
            continue
        if parsed.path == base.path.rstrip("/") + "/equipo/invitacion":
            return candidate, "Revisar invitación"
        if parsed.path == base.path.rstrip("/") + "/cuenta/confirmar":
            purpose = query.get("purpose", [])
            labels = {"verify": "Confirmar mi correo", "reset": "Recuperar mi acceso", "email": "Confirmar nuevo correo"}
            if len(purpose) == 1 and purpose[0] in labels:
                return candidate, labels[purpose[0]]
    return None


def render_email(subject, body, *, public_app_url=""):
    action = _action(body, public_app_url)
    title = subject.removeprefix("TalentSync — ")
    content = body
    if action:
        content = content.replace(action[0], "").replace(". Abre \n", ".\n")
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", content.strip()):
        if paragraph.strip() == "TalentSync":
            continue
        text = "<br>".join(escape(line.rstrip(" :")) for line in paragraph.splitlines())
        paragraphs.append(f'<p style="margin:0 0 18px;font-size:16px;line-height:1.7;color:#475569">{text}</p>')
    button = ""
    if action:
        url, label = escape(action[0], quote=True), escape(action[1])
        button = f'''<table role="presentation" cellpadding="0" cellspacing="0" style="margin:26px 0"><tr><td bgcolor="#06b6d4" style="border-radius:10px;text-align:center;mso-padding-alt:16px 26px">
<a href="{url}" style="display:inline-block;padding:16px 26px;border:1px solid #06b6d4;border-radius:10px;color:#082f49;font-size:16px;line-height:20px;font-weight:bold;text-decoration:none">{label} &rarr;</a></td></tr></table>
<p style="font-size:12px;line-height:1.7;color:#64748b;margin:0 0 24px">Si el botón no funciona, copia este enlace en tu navegador:<br>
<a href="{url}" style="color:#0e7490;word-break:break-all;overflow-wrap:anywhere">{url}</a></p>'''
    # Inbox previews must not expose account tokens from the body.
    preheader = escape(f"{title[:100]} · Tienes un mensaje de TalentSync.")
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>{escape(subject)}</title>
<style>@media only screen and (max-width:620px){{.outer{{padding:20px 10px!important}}.content{{padding:30px 24px!important}}.heading{{font-size:26px!important}}}}</style></head>
<body style="margin:0;padding:0;background-color:#eef3f8;font-family:Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#eef3f8"><tr><td class="outer" align="center" style="padding:48px 16px">
<!--[if mso]><table role="presentation" width="600" align="center"><tr><td><![endif]-->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;border:1px solid #dce4ee;border-radius:18px;background-color:#ffffff;overflow:hidden">
<tr><td bgcolor="#0f172a" style="padding:28px 32px;border-top:5px solid #22d3ee">
<p style="margin:0;color:#ffffff;font-size:25px;line-height:32px;font-weight:bold;letter-spacing:-1px">Talent<span style="color:#22d3ee">Sync</span></p>
<p style="margin:6px 0 0;color:#a5b4c8;font-size:10px;line-height:16px;font-weight:bold;letter-spacing:2px">CONECTA TU TALENTO CON OPORTUNIDADES</p></td></tr>
<tr><td class="content" style="padding:38px 36px 30px">
<p style="margin:0 0 12px;color:#0e7490;font-size:11px;font-weight:bold;letter-spacing:1.5px;line-height:18px">TU ESPACIO EN TALENTSYNC</p>
<h1 class="heading" style="margin:0 0 24px;color:#0f172a;font-size:30px;line-height:1.25;letter-spacing:-0.7px">{escape(title)}</h1>
{''.join(paragraphs)}{button}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="padding:18px 20px;background-color:#f0f9fc;border-left:3px solid #06b6d4;border-radius:8px">
<p style="margin:0;color:#155e75;font-size:13px;line-height:1.7"><strong>Cuida tu cuenta.</strong> TalentSync nunca te pedirá tu contraseña ni códigos de acceso por correo.</p></td></tr></table>
</td></tr><tr><td style="padding:22px 36px;border-top:1px solid #e2e8f0;background-color:#f8fafc">
<p style="margin:0;color:#475569;font-size:13px;line-height:20px;font-weight:bold">Tu siguiente paso empieza contigo.</p>
<p style="margin:6px 0 0;color:#64748b;font-size:12px;line-height:20px">Mensaje de cuenta de TalentSync.</p></td></tr></table>
<!--[if mso]></td></tr></table><![endif]-->
<p style="margin:20px 0 0;color:#64748b;font-size:11px;line-height:18px">TalentSync &middot; Talento, aprendizaje y oportunidades.</p>
</td></tr></table></body></html>'''
