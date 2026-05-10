import os
import time
import json
import asyncio
import django
from channels.layers import get_channel_layer
from dotenv import load_dotenv

# Set up Django environment so we can use channel_layer outside of the web process
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nba_net.settings')
django.setup()

def poll_live_games():
    """
    Simulates polling a live API (like nba_api Live PlayByPlay) every 5 seconds.
    Computes real-time win probability and pushes to Redis Pub/Sub.
    """
    channel_layer = get_channel_layer()
    print("Live Engine started. Polling every 5 seconds...")
    
    # In production, we'd query the live games here.
    # For now, we simulate a single game updating.
    simulated_game_id = "42500233"
    
    home_score = 100
    away_score = 98
    time_remaining = 300 # seconds
    
    while True:
        try:
            # Simulate a score change
            home_score += 2
            time_remaining -= 5
            
            # Re-calculate live win probability (normally run through XGBoost model)
            # win_prob = model.predict_proba(current_state)[0][1]
            win_prob = 0.55 + (home_score - away_score) * 0.01
            win_prob = max(0.0, min(1.0, win_prob)) # Cap between 0 and 1
            
            payload = {
                'game_id': simulated_game_id,
                'home_score': home_score,
                'away_score': away_score,
                'time_remaining': f"{time_remaining // 60}:{time_remaining % 60:02d}",
                'home_win_prob': round(win_prob, 3),
                'away_win_prob': round(1 - win_prob, 3)
            }
            
            # Push to the Django Channels room group via Redis
            asyncio.run(channel_layer.group_send(
                f'game_{simulated_game_id}',
                {
                    'type': 'game_update',
                    'data': payload
                }
            ))
            
            print(f"Pushed update to game_{simulated_game_id}: {payload}")
            
            if time_remaining <= 0:
                print("Game ended.")
                break
                
            time.sleep(5)
            
        except Exception as e:
            print(f"Error in Live Engine loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    poll_live_games()
