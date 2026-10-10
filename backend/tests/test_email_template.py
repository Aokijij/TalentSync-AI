from app.infrastructure.security.email_template import render_email


def test_email_escapes_untrusted_subject_and_body():
    html = render_email('<img src=x onerror="evil()">', '<script>evil()</script>\n\nHola & adiós')
    assert "<script>" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html and "Hola &amp; adiós" in html


def test_account_link_button_preserves_exact_escaped_url():
    url = "https://app.example.com/cuenta/confirmar?purpose=reset&token=synthetic"
    html = render_email("Recupera tu acceso", f"Recupera tu acceso: {url}\nEste enlace vence en 30 minutos.", public_app_url="https://app.example.com")
    assert "Recuperar mi acceso &rarr;" in html
    assert 'href="https://app.example.com/cuenta/confirmar?purpose=reset&amp;token=synthetic"' in html
    assert "Este enlace vence en 30 minutos." in html
    preheader = html.split("<div", 1)[1].split("</div>", 1)[0]
    assert "synthetic" not in preheader


def test_invitation_on_local_origin_and_subpath():
    url = "http://127.0.0.1:5173/demo/equipo/invitacion?token=synthetic"
    html = render_email("Invitación", f"Abre {url}", public_app_url="http://127.0.0.1:5173/demo/")
    assert "Revisar invitación &rarr;" in html


def test_untrusted_urls_never_become_links():
    for url in ["javascript:evil()", "https://app.example.com.evil.invalid/cuenta/confirmar?purpose=verify&token=x",
                "https://attacker@app.example.com/cuenta/confirmar?purpose=verify&token=x",
                "https://app.example.com:444/cuenta/confirmar?purpose=verify&token=x",
                "https://app.example.com/elsewhere?token=x", "https://app.example.com/cuenta/confirmar?purpose=reset",
                "https://app.example.com/cuenta/confirmar?purpose=unknown&token=x"]:
        assert "href=" not in render_email("Mensaje", url, public_app_url="https://app.example.com")


def test_email_is_self_contained_and_readable_without_images():
    html = render_email("Prueba", "Hola, José.\n\nConexión preparada.")
    assert "<html lang=\"es\">" in html and "max-width:600px" in html
    assert "@media" in html and "role=\"presentation\"" in html
    assert "<img" not in html and "<script" not in html and "src=" not in html
