import urllib.request
import json
import sys

# Ensure stdout handles UTF-8 safely
sys.stdout.reconfigure(encoding='utf-8')

def test():
    test_slugs = ['svc-aadhaar', 'svc-dl', 'svc-pmjay', 'svc-passport', 'svc-pan', 'svc-amrut']
    print("=== Testing Services Slugs ===")
    for s in test_slugs:
        try:
            url = f"http://localhost:8000/api/v1/services/{s}"
            with urllib.request.urlopen(url) as res:
                data = json.loads(res.read().decode("utf-8"))
                svc = data["data"]
                cat_name = svc.get("category", {}).get("name") if svc.get("category") else "None"
                dept_name = svc.get("department", {}).get("name") if svc.get("department") else "None"
                steps_count = len(svc.get("application_steps", []))
                docs_count = len(svc.get("documents", []))
                faqs_count = len(svc.get("faqs", []))
                print(f"[OK] /services/{s:<15} -> {svc['name']} | Dept: {dept_name} | Steps: {steps_count} | Docs: {docs_count} | FAQs: {faqs_count}")
        except Exception as e:
            print(f"[FAIL] /services/{s:<15} -> Error: {e}")

    print("\n=== Testing Schemes Slugs ===")
    try:
        with urllib.request.urlopen("http://localhost:8000/api/v1/schemes?page_size=5") as res:
            sch_data = json.loads(res.read().decode("utf-8"))
            for sc in sch_data["data"]["items"]:
                sc_slug = sc["slug"]
                url = f"http://localhost:8000/api/v1/schemes/{sc_slug}"
                with urllib.request.urlopen(url) as s_res:
                    s_data = json.loads(s_res.read().decode("utf-8"))["data"]
                    print(f"[OK] /schemes/{sc_slug:<20} -> {s_data['name']} | Beneficiary: {s_data.get('target_beneficiary')}")
    except Exception as e:
        print(f"[FAIL] Schemes test error: {e}")

if __name__ == "__main__":
    test()
