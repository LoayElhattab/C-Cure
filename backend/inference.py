import requests
import os


class InferenceClient:
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

    def __init__(self, api_url: str = None):
        self.api_url = api_url or os.environ.get(
            "KAGGLE_API_URL",
            "https://your-ngrok-url-here.ngrok-free.app"
        )

    def check_health(self) -> bool:
        try:
            r = requests.get(f"{self.api_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def analyze_function(self, code: str) -> dict:
        try:
            # Step 1: Triage
            triage = requests.post(
                f"{self.api_url}/triage",
                json={"code": code},
                timeout=30
            )
            triage.raise_for_status()
            family = triage.json().get("family", "safe")

            if family == "safe":
                return {
                    "verdict": "safe",
                    "cwe": None, "cwe_name": None,
                    "severity": None, "confidence": None, "family": None,
                }

            # Step 2: Classify
            classify = requests.post(
                f"{self.api_url}/classify",
                json={"code": code, "family": family},
                timeout=30
            )
            classify.raise_for_status()
            data = classify.json()
            cwe = data.get("cwe")
            cwe_meta = self.CWE_INFO.get(cwe, {"name": "Unknown", "severity": "Unknown"})

            return {
                "verdict": "vulnerable",
                "cwe": cwe,
                "cwe_name": cwe_meta["name"],
                "severity": cwe_meta["severity"],
                "confidence": data.get("confidence"),
                "family": family,
            }

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot reach Kaggle API. Is the notebook running?"}
        except requests.exceptions.Timeout:
            return {"error": "Kaggle API timed out."}
        except Exception as e:
            return {"error": str(e)}


# Global singleton
client = InferenceClient()