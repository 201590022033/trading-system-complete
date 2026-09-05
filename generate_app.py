import os
from dotenv import load_dotenv
from openai import OpenAI
from app import INDEX_HTML

load_dotenv()

API_KEY = os.environ["MOONSHOT_API_KEY"]
BASE_URL = "https://api.moonshot.ai/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# The dashboard is embedded in app.py and rendered with render_template_string().
html_code = INDEX_HTML
print("📦 Successfully loaded embedded dashboard UI from: 'app.py:INDEX_HTML'")

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
    print(completion.choices[0].message.content)
except Exception as e:
    print(f"\n❌ Network Transaction Failed: {e}")
