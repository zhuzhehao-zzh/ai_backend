#!/usr/bin/env python3
"""
Cloud deployment test suite.
Run this after any change to verify the backend is working correctly.

Usage:
    # Test locally (if server accessible directly)
    python3 test_cloud.py

    # Test via SSH (for internal-only backends)
    python3 test_cloud.py --ssh
"""
import json
import sys
import os
import subprocess

BASE_URL = "http://localhost:8000"
SSH_HOST = "101.43.30.20"
SSH_USER = "ubuntu"
SSH_PASS = "Openclaw930721"

SAMPLE_STUDENT = {
    "subjectTrack": "理科",
    "province": "广东",
    "score": 610,
    "interests": "写代码、研究 AI、解决工程问题",
    "skills": "数学能力、逻辑推理、自学能力",
    "preferences": "高收入潜力、技术壁垒、稳定性",
    "preferredCities": ["深圳", "杭州"],
    "dislikes": "不想学医、不接受高压行业",
}

EXPECTED_KEYS = {"report_id", "generated_at", "profileSummary", "top", "cautious", "all"}
EXPECTED_TOP_KEYS = {"id", "name", "recommendationBand", "matchScore", "aiRisk",
                     "outlook", "competitiveness", "summary", "schoolStrategy",
                     "cities", "companies", "roles", "yearPlan"}
EXPECTED_YEARPLAN_KEYS = {"year1", "year2", "year3", "year4"}

passed = 0
failed = 0


def run_curl(method, path, data=None, timeout=120):
    """Run curl and return (status_code, response_json, error)."""
    url = f"{BASE_URL}{path}"
    cmd = ["curl", "-s", "-o", "/tmp/_test_output.json", "-w", "%{http_code}",
           "--max-time", str(timeout), "-X", method, url]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data, ensure_ascii=False)]
    
    if "--ssh" in sys.argv:
        # Run via SSH
        data_arg = f"""'{json.dumps(data, ensure_ascii=False).replace("'", "'\\''")}'""" if data else ""
        curl_cmd = f"curl -s -o /tmp/_test_output.json -w '%{{http_code}}' --max-time {timeout} -X {method} {url}"
        if data:
            curl_cmd += f" -H 'Content-Type: application/json' -d {data_arg}"
        
        ssh_cmd = f"sshpass -p '{SSH_PASS}' ssh -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} '{curl_cmd}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout + 10)
        status = result.stdout.strip()
        error = result.stderr.strip()
        
        # Read the response
        get_cmd = f"sshpass -p '{SSH_PASS}' ssh -o StrictHostKeyChecking=no {SSH_USER}@{SSH_HOST} 'cat /tmp/_test_output.json'"
        result = subprocess.run(get_cmd, shell=True, capture_output=True, text=True, timeout=10)
        body = result.stdout.strip()
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        status = result.stdout.strip()
        error = result.stderr.strip()
        try:
            with open("/tmp/_test_output.json") as f:
                body = f.read().strip()
        except FileNotFoundError:
            body = ""
    
    try:
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        data = {}
    
    return status, data, error


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")


print("=" * 60)
print("  Cloud Backend Test Suite")
print("=" * 60)
print()

# 1. Health check
print("[1] Health Check")
status, data, err = run_curl("GET", "/health", timeout=5)
check("Health endpoint returns 200", status == "200", f"got {status}")
check("Health returns ok", data.get("status") == "ok", str(data))

# 2. Submit valid student
print("\n[2] Submit Valid Student")
status, data, err = run_curl("POST", "/api/submit", SAMPLE_STUDENT, timeout=120)
check("Submit returns 200", status == "200", f"got {status}")

if status == "200":
    check("Has report_id", "report_id" in data)
    check("Has generated_at", "generated_at" in data)
    check("Has profileSummary", "profileSummary" in data)
    check("Has top list", "top" in data and len(data["top"]) > 0)
    check("Has cautious", "cautious" in data)
    check("Has all", "all" in data)
    check("Correct top keys", all(k in data["top"][0] for k in EXPECTED_TOP_KEYS),
          f"missing: {EXPECTED_TOP_KEYS - set(data['top'][0].keys())}")
    
    top_item = data["top"][0]
    if "yearPlan" in top_item:
        check("yearPlan has 4 years", all(k in top_item["yearPlan"] for k in EXPECTED_YEARPLAN_KEYS),
              f"missing: {EXPECTED_YEARPLAN_KEYS - set(top_item['yearPlan'].keys())}")
        check("year1 has suggestions", len(top_item["yearPlan"].get("year1", [])) > 0)
    
    ps = data["profileSummary"]
    check("profileSummary has cluster", "cluster" in ps and ps["cluster"])
    
    match_scores = [t.get("matchScore", 0) for t in data["top"]]
    check("matchScores are 0-100", all(0 <= s <= 100 for s in match_scores),
          f"got scores: {match_scores}")

# 3. Submit with partial data (empty is rejected — LLM needs some context)
print("\n[3] Submit with Partial Data")
status, data, err = run_curl("POST", "/api/submit", {"score": 600}, timeout=120)
check("Partial data returns 200", status == "200", f"got {status}")
check("Has report_id", "report_id" in data)
check("Has profileSummary", "profileSummary" in data)

# 4. Different field names work (backend is field-agnostic)
print("\n[4] Custom Field Names")
status, data, err = run_curl("POST", "/api/submit",
    {"score": 610, "interests": "编程", "city": "深圳"}, timeout=120)
check("Custom fields returns 200", status == "200", f"got {status}")
check("Has recommendations", len(data.get("top", [])) > 0)

# 5. Response time check (informational)
print("\n[5] Response Time")
print("  (Response time depends on Kimi API — typically 30-60s)")

print()
print("=" * 60)
print(f"  Results: {passed} passed, {failed} failed")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
