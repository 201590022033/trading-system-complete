import os
from openai import OpenAI

# 1. Put your real Kimi developer token inside the quotes
API_KEY = "sk-bqKmPtr5lS9KWaOptg8DMIHLquev4rDCFrahSf6Yd3UcDDb1"
BASE_URL = "https://moonshot.ai"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 2. Automatically locate your HTML dashboard wherever it is hiding
ui_file_path = None
possible_paths = ["index.html", "templates/index.html", "web/index.html", "src/index.html"]

for path in possible_paths:
    if os.path.exists(path):
        ui_file_path = path
        break

if not ui_file_path:
    print("❌ Error: Could not find your dashboard index.html file anywhere in the workspace!")
    exit()

try:
    with open(ui_file_path, "r") as f:
        html_code = f.read()
    print(f"📦 Successfully found and loaded your UI file from: '{ui_file_path}'")
except Exception as e:
    print(f"❌ Error reading file: {e}")
    exit()

prompt = f"""
I am streaming live JSE trading ticks every single second via Flask-SocketIO. 
Look at my user interface script code below. Does my JavaScript socket message handler 
have a mechanism or sliding window to cap the incoming data array length? 
If it doesn't, tell me why it will cause a browser cache memory crash over time, 
and write out the exact, corrected block of JavaScript code to limit it to the last 100 ticks.

Here is my UI Code:
{html_code}
"""

try:
    print("🤖 Querying Kimi K3 deep-thinking model to audit your memory leak...")
    completion = client.chat.completions.create(
        model="kimi-k3",
        messages=[{"role": "user", "content": prompt}]
    )
    print("\n--- 📊 KIMI K3 AUDIT RESULTS ---")
    print(completion.choices.message.content)
except Exception as e:
    print(f"\n❌ Network Transaction Failed: {e}")
