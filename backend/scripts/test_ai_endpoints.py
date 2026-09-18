import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test():
    print("=== Testing AI Health ===")
    try:
        url = "http://localhost:8000/api/v1/ai/health"
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read().decode("utf-8"))
            print("Health Response:", json.dumps(data, indent=2))
    except Exception as e:
        print("Health Error:", e)

    print("\n=== Testing AI Chat ('Hi') ===")
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/ai/chat",
            data=json.dumps({"message": "Hi, I need help with government services."}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            print("Chat Response (Hi):\n", data["data"]["content"][:300] + "...")
            print("Sources:", data["data"].get("sources"))
    except Exception as e:
        print("Chat Error (Hi):", e)

    print("\n=== Testing AI Chat ('How to apply for Aadhaar?') ===")
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/ai/chat",
            data=json.dumps({"message": "How to apply for Aadhaar?"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            print("Chat Response (Aadhaar):\n", data["data"]["content"][:400] + "...")
            print("Sources:", data["data"].get("sources"))
    except Exception as e:
        print("Chat Error (Aadhaar):", e)

if __name__ == "__main__":
    test()
