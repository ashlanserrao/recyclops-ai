"""Security headers sent with every response, the API's and the built site's alike.

frontend/vercel.json repeats them for the site on Vercel; a test checks the two match.
"""

SECURITY_HEADERS = {
    # Everything comes from our own origin: Vercel forwards /api/* to the backend, so no other host is contacted.
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    # Geolocation powers "use my location", on our own pages only.
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",
    "Cross-Origin-Opener-Policy": "same-origin",
}
# Sent only over HTTPS: browsers ignore it on plain HTTP, and localhost stays usable.
HSTS = "max-age=31536000"
