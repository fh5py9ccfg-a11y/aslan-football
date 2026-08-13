from __future__ import annotations

import html
import json
from http.cookies import SimpleCookie

from aslan_ozaslan.auth import Permission, RoleAuthorizer
from aslan_ozaslan.security import CookiePolicy, CsrfManager, LoginAttemptGuard, SessionManager


def create_app(title: str = "Aslan Özaslan"):
    sessions = SessionManager(ttl_minutes=60)
    csrf = CsrfManager()
    lockout = LoginAttemptGuard(max_failures=5, lock_minutes=15)
    authorizer = RoleAuthorizer()
    cookie_policy = CookiePolicy()

    demo_token = sessions.create("demo-owner", "OWNER")
    demo_csrf = csrf.issue(demo_token)

    def json_response(start_response, status, payload, extra_headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
        ]
        if extra_headers:
            headers.extend(extra_headers)
        start_response(status, headers)
        return [body]

    def get_cookie(environ, name):
        raw = environ.get("HTTP_COOKIE", "")
        cookie = SimpleCookie()
        cookie.load(raw)
        morsel = cookie.get(name)
        return morsel.value if morsel else ""

    def get_session_token(environ):
        return (
            get_cookie(environ, cookie_policy.name)
            or environ.get("HTTP_X_SESSION_TOKEN", "")
        )

    def app(environ, start_response):
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")

        if path == "/health" and method == "GET":
            return json_response(
                start_response,
                "200 OK",
                {"status": "ok", "service": "aslan-ozaslan", "version": "2.2"},
            )

        if path == "/demo-session" and method == "GET":
            return json_response(
                start_response,
                "200 OK",
                {"session_token": demo_token, "csrf_token": demo_csrf},
                extra_headers=[("Set-Cookie", cookie_policy.header(demo_token))],
            )

        if path == "/logout" and method == "POST":
            session_token = get_session_token(environ)
            csrf_token = environ.get("HTTP_X_CSRF_TOKEN", "")
            if not csrf.validate(session_token, csrf_token):
                return json_response(start_response, "403 Forbidden", {"error": "csrf_failed"})
            sessions.revoke(session_token)
            return json_response(
                start_response,
                "200 OK",
                {"status": "logged_out"},
                extra_headers=[("Set-Cookie", cookie_policy.clear_header())],
            )

        if path == "/fixtures" and method == "GET":
            session_token = get_session_token(environ)
            record = sessions.validate(session_token)
            if record is None:
                return json_response(start_response, "401 Unauthorized", {"error": "unauthorized"})
            try:
                authorizer.require(record.role, Permission.VIEW_ANALYSIS)
            except PermissionError:
                return json_response(start_response, "403 Forbidden", {"error": "forbidden"})
            return json_response(
                start_response,
                "200 OK",
                {
                    "fixtures": [],
                    "message": "Gerçek veri sağlayıcısı bağlanana kadar fikstür listesi boş tutulur.",
                },
            )

        if path == "/analysis" and method == "GET":
            session_token = get_session_token(environ)
            record = sessions.validate(session_token)
            if record is None:
                return json_response(start_response, "401 Unauthorized", {"error": "unauthorized"})
            try:
                authorizer.require(record.role, Permission.VIEW_ANALYSIS)
            except PermissionError:
                return json_response(start_response, "403 Forbidden", {"error": "forbidden"})
            return json_response(
                start_response,
                "200 OK",
                {
                    "status": "not_ready",
                    "message": "Gerçek veri ve doğrulanmış model olmadan tahmin gösterilmez.",
                    "model_version": "v1.9-e2e",
                },
            )

        if path == "/analysis/run" and method == "POST":
            session_token = get_session_token(environ)
            csrf_token = environ.get("HTTP_X_CSRF_TOKEN", "")
            record = sessions.validate(session_token)
            if record is None:
                return json_response(start_response, "401 Unauthorized", {"error": "unauthorized"})
            if not csrf.validate(session_token, csrf_token):
                return json_response(start_response, "403 Forbidden", {"error": "csrf_failed"})
            try:
                authorizer.require(record.role, Permission.RUN_ANALYSIS)
            except PermissionError:
                return json_response(start_response, "403 Forbidden", {"error": "forbidden"})
            return json_response(
                start_response,
                "503 Service Unavailable",
                {
                    "status": "blocked",
                    "message": "Gerçek sağlayıcı bağlantısı ve doğrulanmış veri olmadan analiz çalıştırılmaz.",
                },
            )

        if path == "/" and method == "GET":
            body = f'''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui;margin:0;background:#0f172a;color:#e2e8f0}}
main{{max-width:920px;margin:48px auto;padding:24px}}
.card{{background:#111c35;border:1px solid #334155;border-radius:16px;padding:24px;margin-bottom:16px}}
.badge{{display:inline-block;background:#1e293b;padding:6px 10px;border-radius:999px}}
h1{{margin-top:12px}} p{{line-height:1.6;color:#cbd5e1}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.metric{{background:#0b1224;border:1px solid #24324a;border-radius:12px;padding:16px}}
</style>
</head>
<body>
<main>
<div class="card">
<span class="badge">v2.2 kalıcı oturum ve fikstür temeli</span>
<h1>{html.escape(title)}</h1>
<p>Gerçek veri ve doğrulanmış model olmadan tahmin gösterilmez.</p>
</div>
<div class="grid">
<div class="metric"><strong>Oturum</strong><p>Kalıcı depoya taşınabilir yapı hazır.</p></div>
<div class="metric"><strong>Cookie</strong><p>HttpOnly, Secure ve SameSite politikası hazır.</p></div>
<div class="metric"><strong>Fikstür</strong><p>Kalıcı kayıt ve sıralı liste altyapısı hazır.</p></div>
<div class="metric"><strong>Çıkış</strong><p>Oturum iptali ve cookie temizleme hazır.</p></div>
</div>
</main>
</body>
</html>'''.encode("utf-8")
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("X-Content-Type-Options", "nosniff"),
                    ("Referrer-Policy", "no-referrer"),
                ],
            )
            return [body]

        return json_response(start_response, "404 Not Found", {"error": "not_found"})

    return app
