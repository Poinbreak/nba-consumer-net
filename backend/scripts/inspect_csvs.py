import pandas as pd

# Check TeamStatistics columns
ts = pd.read_csv('backend/data/TeamStatistics.csv')
print("=== TEAM STATS COLUMNS ===")
print(ts.columns.tolist())
print("\nSample row:")
print(ts.iloc[0].to_dict())

print("\n=== PLAYER STATS COLUMNS ===")
ps = pd.read_csv('backend/data/PlayerStatistics.csv', nrows=2)
print(ps.columns.tolist())
print("\nSample row:")
print(ps.iloc[0].to_dict())
