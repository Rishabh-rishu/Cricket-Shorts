"""
YouTube OAuth 2.0 Re-authentication Utility (Dual-Mode: Auto Server + URL Paste)
Generates a fresh token.pickle with offline access (refresh_token),
exports base64 string to token_pickle_base64.txt, and verifies with YouTube API.
"""

import os
import sys
import pickle
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_PICKLE_FILE = "token.pickle"
BASE64_OUTPUT_FILE = "token_pickle_base64.txt"
PORT = 8088


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_response_url = None

    def do_GET(self):
        OAuthCallbackHandler.auth_response_url = self.path
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = """
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #f0fdf4;">
            <h1 style="color: #166534;">✓ Authentication Successful!</h1>
            <p style="font-size: 18px; color: #15803d;">You can now close this tab and return to your terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        # Silence default HTTP server logging
        return


def start_local_server():
    server = HTTPServer(("0.0.0.0", PORT), OAuthCallbackHandler)
    server.timeout = 300  # 5 minutes
    server.handle_request()
    server.server_close()


def main():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"✗ Error: '{CLIENT_SECRETS_FILE}' not found in current directory.")
        return

    redirect_uri = f"http://localhost:{PORT}/"
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES,
        redirect_uri=redirect_uri
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

    print("\n" + "=" * 70)
    print("  🏏 CRICKET SHORTS - YOUTUBE OAUTH 2.0 RE-AUTHENTICATION")
    print("=" * 70)
    print("\nSTEP 1: Open this authorization link in your web browser:")
    print("-" * 70)
    print(auth_url)
    print("-" * 70)

    # Start background server
    server_thread = threading.Thread(target=start_local_server, daemon=True)
    server_thread.start()

    print("\nSTEP 2: Sign in with your YouTube channel account and click 'Allow'.")
    print("\n👉 If your browser redirects automatically, the terminal will finish.")
    print("👉 If your browser shows 'This site can't be reached', simply COPY the")
    print("   entire URL from your browser address bar and PASTE it below:\n")

    auth_code_or_url = None
    try:
        # Check if auto server received response or prompt user
        import select
        print("Paste Redirect URL (or press Enter if waiting for auto-detect): ", end="", flush=True)
        user_input = sys.stdin.readline().strip()
        if user_input:
            auth_code_or_url = user_input
    except Exception:
        pass

    # If user didn't paste, wait briefly for server thread
    if not auth_code_or_url:
        print("Waiting for browser redirect on localhost:8088...")
        server_thread.join(timeout=60)
        if OAuthCallbackHandler.auth_response_url:
            auth_code_or_url = f"http://localhost:{PORT}{OAuthCallbackHandler.auth_response_url}"

    if not auth_code_or_url:
        print("\nDid not receive redirect automatically.")
        auth_code_or_url = input("Please paste the full address bar URL here: ").strip()

    if not auth_code_or_url:
        print("✗ Error: No authorization response received.")
        return

    # Normalize url
    if not auth_code_or_url.startswith("http"):
        if "code=" in auth_code_or_url:
            auth_code_or_url = f"http://localhost:{PORT}/?{auth_code_or_url}"
        else:
            auth_code_or_url = f"http://localhost:{PORT}/?code={auth_code_or_url}"

    try:
        flow.fetch_token(authorization_response=auth_code_or_url)
    except Exception as e:
        print(f"\n✗ Token exchange error: {e}")
        # Try extracting code directly
        parsed = urllib.parse.urlparse(auth_code_or_url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]
            try:
                flow.fetch_token(code=code)
            except Exception as e2:
                print(f"✗ Direct code exchange also failed: {e2}")
                return
        else:
            return

    creds = flow.credentials
    if not creds:
        print("✗ Authentication failed: No credentials returned.")
        return

    # Save to token.pickle
    with open(TOKEN_PICKLE_FILE, "wb") as f:
        pickle.dump(creds, f)
    print(f"\n✓ Saved fresh OAuth token to '{TOKEN_PICKLE_FILE}'.")

    # Generate base64 string
    with open(TOKEN_PICKLE_FILE, "rb") as f:
        b64_str = base64.b64encode(f.read()).decode("utf-8")

    with open(BASE64_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(b64_str)
    print(f"✓ Saved base64 string to '{BASE64_OUTPUT_FILE}'.")

    # Verify token by making a live read call
    try:
        service = build("youtube", "v3", credentials=creds)
        res = service.channels().list(part="snippet", mine=True).execute()
        channels = res.get("items", [])
        if channels:
            ch_title = channels[0]["snippet"]["title"]
            print(f"✓ VERIFIED: Successfully connected to YouTube Channel: '{ch_title}'!")
        else:
            print("✓ VERIFIED: Connected to YouTube account.")
    except Exception as e:
        print(f"⚠ Warning: Channel verification call: {e}")

    print("\n" + "=" * 70)
    print("  COPY THIS NEW BASE64 SECRET VALUE FOR GITHUB ACTIONS:")
    print("=" * 70)
    print(b64_str)
    print("=" * 70)
    print("\n1. Go to GitHub repo -> Settings -> Secrets and variables -> Actions")
    print("2. Edit secret 'YOUTUBE_TOKEN_PICKLE_BASE64' and paste the string above.")
    print("3. (Optional) If 'YOUTUBE_TOKEN_BASE64' exists, update it too.")
    print("4. Re-run your GitHub Actions workflow!\n")


if __name__ == "__main__":
    main()
