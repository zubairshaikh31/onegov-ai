"""
OneGov AI — Live Chat API Tester
"""
import urllib.request
import json
import sys

# Ensure stdout/stderr handles UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    url = "http://localhost:8000/api/v1/ai/chat"
    headers = {"Content-Type": "application/json"}
    body = {
        "message": "Show me how to apply for a fresh passport",
        "session_id": "live-test-session"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        print("Sending request to live chatbot endpoint...")
        with urllib.request.urlopen(req, timeout=120) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            print("="*70)
            print("CHATBOT RESPONSE:")
            print("="*70)
            print(res_data["data"]["content"])
            print("="*70)
            print("SOURCES / CITATIONS:")
            print("="*70)
            for src in res_data["data"]["sources"]:
                print(f"- [{src['type'].upper()}] {src['title']} ({src['slug']}) -> {src['url']}")
    except Exception as exc:
        print(f"Request failed: {exc}")

if __name__ == "__main__":
    main()
