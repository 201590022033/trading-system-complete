import os
import json
from openai import OpenAI

# 1. Put your raw Kimi developer API key inside the quotes
API_KEY = "sk-bqKmPtr5lS9KWaOptg8DMIHLquev4rDCFrahSf6Yd3UcDDb1"
BASE_URL = "https://api.moonshot.ai/v1"

print("🔄 Initializing secure SDK connection...")
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

prompt = """
Write a complete, clean, operational app.py file for a JSE trading prototype system. 
It must initialize a standard Flask app integrated with Flask-SocketIO. 
Include a background worker thread that simulates streaming asset price ticker data, 
and uses socketio.emit to push JSON updates to a local UI. 
Make sure the server executes using socketio.run(app, host='0.0.0.0', port=5000). 
Give me ONLY raw python code, no markdown code block text fences.
"""

try:
    print("🤖 Directly querying Kimi via SDK to build app.py...")
    completion = client.chat.completions.create(
        model="kimi-k3",
        messages=[{"role": "user", "content": prompt}]
    )
    
    code = completion.choices[0].message.content
    
    # Strip any accidental formatting markdown blocks if the AI includes them
    code = code.replace("```python", "").replace("```", "")
    
    with open("app.py", "w") as f:
        f.write(code.strip())
    print("\n✅ Success! Your app.py file has been built successfully.")

except Exception as e:
    print("\n❌ SDK Request Failed!")
    print(f"Error Details: {e}")
