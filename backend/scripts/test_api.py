import urllib.request, json

# Test prediction for the first real game
game_id = "42500233"
r = urllib.request.urlopen(f'http://localhost:8000/api/predictions/game/{game_id}/')
d = json.load(r)
print("=== PREDICTION ===")
print(f"Home win prob: {d.get('home_win_probability')}")
print(f"Predicted score: {d.get('predicted_score')}")
print(f"SHAP factors: {len(d.get('shap_factors', []))}")
for f in d.get('shap_factors', []):
    print(f"  {f['feature']}: {f['impact']} - {f['description']}")

print()

# Test odds endpoint
try:
    r2 = urllib.request.urlopen('http://localhost:8000/api/odds/')
    d2 = json.load(r2)
    print(f"=== ODDS === {len(d2)} games with odds")
    if d2:
        print(f"Sample: {json.dumps(d2[0], indent=2)[:300]}")
except Exception as e:
    print(f"Odds error (expected if no key): {e}")
