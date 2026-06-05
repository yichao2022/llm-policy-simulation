#!/usr/bin/env python3
"""Orientation battery for 6 OpenRouter expansion models. 1 call per model, 20 items."""

import csv, json, os, re, time, requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
PROJECT = Path(__file__).resolve().parent
KEY = os.environ['OPENROUTER_API_KEY']
OR_BASE = "https://openrouter.ai/api/v1"

# Load models
MODELS = list(csv.DictReader(open(PROJECT / "inputs/models_expanded_openrouter_additions.csv")))

# Load orientation items
orient_rows = list(csv.DictReader(open(PROJECT / "data/orientation_responses.csv")))
# Get unique items (first model's 20 items, sorted by item_order)
items = []
seen = set()
for r in orient_rows:
    if r['item_id'] not in seen:
        seen.add(r['item_id'])
        items.append({'item_id': r['item_id'], 'item_text': r['item_text'],
                      'dimension': r['dimension'], 'reverse_coded': r['reverse_coded'],
                      'item_order': int(r['item_order'])})
items.sort(key=lambda x: x['item_order'])
print(f"Items: {len(items)}")

# Prompt
SYSTEM_PROMPT = (
    "You are a policy analyst completing a survey. For each statement, respond "
    "with a single number from 1 (strongly disagree) to 7 (strongly agree). "
    "Output only the number."
)

def build_user_prompt():
    lines = ["Rate the following 20 statements (1-7):\n"]
    for item in items:
        lines.append(f"{item['item_order']}. {item['item_text']}")
    lines.append("\nRespond with ONLY your score (1-7) for each statement, one per line. Example:\n6\n3\n5\n4\n...")
    return "\n".join(lines)

USER_PROMPT = build_user_prompt()

OUT_FILE = PROJECT / "outputs/openrouter_expansion/orientation_raw.csv"
OUT_FIELDS = ['model','provider','access_route','requested_model_id','returned_model_id',
              'route_provider','item_id','dimension','reverse_coded',
              'raw_response','parsed_score','valid_score','timestamp','temperature','top_p','metadata_json']

MAX_RETRIES = 4

def call_or(model_id, model_name, temp=0):
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    max_tok = 300
    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        "temperature": temp, "max_tokens": max_tok,
    }
    # Disable reasoning for Kimi (otherwise too slow)
    if 'kimi' in model_name.lower():
        body['reasoning'] = {'enabled': False}
        body['max_tokens'] = 300  # no reasoning needed, lower tokens
    r = requests.post(f"{OR_BASE}/chat/completions", headers=headers, json=body, timeout=120)
    r.raise_for_status()
    return r.json()

def parse_numbers(raw):
    if raw is None: return []
    """Extract up to 20 numbers from response."""
    nums = re.findall(r'\b([1-7])\b', raw)
    return [int(n) for n in nums[:20]]

# Resume
completed_models = set()
if OUT_FILE.exists():
    with open(OUT_FILE) as f:
        for row in csv.DictReader(f):
            completed_models.add(row['model'])

all_rows = []
file_exists = OUT_FILE.exists()

for m in MODELS:
    model_name = m['model']
    if model_name in completed_models:
        print(f"[SKIP] {model_name}")
        continue

    print(f"[RUN] {model_name} → {m['requested_model_id']}")
    
    raw = ""; metadata = {}; returned_id = ""; route = ""
    err = ""
    for attempt in range(1, MAX_RETRIES+1):
        try:
            resp = call_or(m['requested_model_id'], m['model'])
            raw = resp['choices'][0]['message']['content']
            returned_id = resp.get('model', '')
            metadata = {
                'id': resp.get('id',''), 'model': resp.get('model',''),
                'provider': resp.get('provider',''),
            }
            break
        except Exception as e:
            err = str(e)
            if attempt < MAX_RETRIES:
                print(f"  [retry {attempt}] {err[:100]}")
                time.sleep(2 ** attempt)
            else:
                print(f"  [FAILED] {err[:150]}")
                raw = ""

    scores = parse_numbers(raw)
    ts = datetime.now(timezone.utc).isoformat()

    for i, item in enumerate(items):
        if i < len(scores):
            parsed = scores[i]
            valid = 1 if 1 <= parsed <= 7 else 0
        else:
            parsed = ""
            valid = 0

        row = {
            'model': model_name, 'provider': m['provider'], 'access_route': m['access_route'],
            'requested_model_id': m['requested_model_id'], 'returned_model_id': returned_id,
            'route_provider': metadata.get('provider',''),
            'item_id': item['item_id'], 'dimension': item['dimension'],
            'reverse_coded': item['reverse_coded'], 'raw_response': raw,
            'parsed_score': parsed, 'valid_score': valid, 'timestamp': ts,
            'temperature': 0, 'top_p': m['top_p'],
            'metadata_json': json.dumps(metadata),
        }
        all_rows.append(row)

    # Write incrementally
    with open(OUT_FILE, 'w' if not file_exists else 'a', newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        if not file_exists:
            w.writeheader()
            file_exists = True
        w.writerows(all_rows[-20:])
    
    time.sleep(0.3)

print(f"\nDone. Total rows: {len(all_rows)} → {OUT_FILE}")
