import os
import json
from flask import Flask, request, jsonify  # Or adapt to your Python framework (FastAPI, etc.)
import urllib.request

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        persona = data.get('persona', 'Exam Prep Coach')
        
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return jsonify({'reply': 'Server configuration error: Missing OpenRouter API Key.'}), 500

        # Define system prompts based on your personas
        system_prompt = "You are Gyan, an intelligent multi-persona AI companion."
        if persona == 'Exam Prep Coach':
            system_prompt = "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly."
        elif persona == 'Strict Professor':
            system_prompt = "You are a strict, academic professor who demands rigorous precision and high standards."
        elif persona == 'Senior Tech Lead':
            system_prompt = "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance."
        elif persona == 'Data Science Mentor':
            system_prompt = "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines."
        elif persona == 'Creative Director':
            system_prompt = "You are a Creative Director focusing on design principles, typography, and visual aesthetics."

        formatted_messages = [{'role': 'system', 'content': system_prompt}] + messages

        # Call OpenRouter API
        payload = json.dumps({
            "model": "meta-llama/llama-3-8b-instruct:free",
            "messages": formatted_messages
        }).encode('utf-8')

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://your-site.netlify.app",
                "X-Title": "Gyan AI",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            if 'error' in res_data:
                return jsonify({'reply': 'AI Error: ' + res_data['error'].get('message', 'Unknown error')}), 400

            reply = res_data['choices'][0]['message']['content'] if res_data.get('choices') else 'No response generated.'
            return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'reply': 'Server error: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
