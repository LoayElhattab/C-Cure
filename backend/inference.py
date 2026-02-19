import requests

# Your ML teammate pastes their ngrok URL here when the notebook is running
KAGGLE_API_URL = "https://your-ngrok-url-here.ngrok-free.app"

FAMILY_MAP = {
    "memory_corruption": ["CWE-125", "CWE-787"],
    "input_validation":  ["CWE-190", "CWE-369"],
    "memory_lifecycle":  ["CWE-415", "CWE-476"],
}

CWE_INFO = {
    "CWE-125": {"name": "Out-of-bounds Read",       "severity": "High"},
    "CWE-787": {"name": "Out-of-bounds Write",      "severity": "Critical"},
    "CWE-190": {"name": "Integer Overflow",         "severity": "Medium"},
    "CWE-369": {"name": "Divide By Zero",           "severity": "Medium"},
    "CWE-415": {"name": "Double Free",              "severity": "High"},
    "CWE-476": {"name": "NULL Pointer Dereference", "severity": "High"},
}


def check_api_health() -> bool:
    try:
        r = requests.get(f"{KAGGLE_API_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def analyze_function(code: str) -> dict:
    """
    Run a single function through triage → classify.
    Returns a result dict ready to be saved to SQLite.
    """
    try:
        # Step 1: Triage
        triage_response = requests.post(
            f"{KAGGLE_API_URL}/triage",
            json={"code": code},
            timeout=30
        )
        triage_response.raise_for_status()
        family = triage_response.json().get("family", "safe")

        # Step 2: If safe, return early
        if family == "safe":
            return {
                "verdict": "safe",
                "cwe": None,
                "cwe_name": None,
                "severity": None,
                "confidence": None,
                "family": None,
            }

        # Step 3: Classify
        classify_response = requests.post(
            f"{KAGGLE_API_URL}/classify",
            json={"code": code, "family": family},
            timeout=30
        )
        classify_response.raise_for_status()
        data = classify_response.json()
        cwe = data.get("cwe")
        confidence = data.get("confidence")

        cwe_meta = CWE_INFO.get(cwe, {"name": "Unknown", "severity": "Unknown"})

        return {
            "verdict": "vulnerable",
            "cwe": cwe,
            "cwe_name": cwe_meta["name"],
            "severity": cwe_meta["severity"],
            "confidence": confidence,
            "family": family,
        }

    except requests.exceptions.ConnectionError:
        return {"error": "Cannot reach Kaggle API. Is the notebook running?"}
    except requests.exceptions.Timeout:
        return {"error": "Kaggle API timed out."}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Quick health check test
    print("Checking API health...")
    if check_api_health():
        print("✓ API is reachable")
    else:
        print("✗ API not reachable — paste your ngrok URL into KAGGLE_API_URL first")