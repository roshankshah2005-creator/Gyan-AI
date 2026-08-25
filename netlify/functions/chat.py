import json
import os
import urllib.request
import urllib.error

def handler(event, context):
    # Only allow POST
    if event.get("httpMethod") != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method Not Allowed"})
        }

    try:
        body = json.loads(event.get("body", "{}"))
        messages = body.get("messages", [])
        persona = body.get("persona", "Exam Prep Coach")
        api_key = os.environ.get("OPENROUTER_API_KEY")

        if not api_key:
            return {
                "statusCode": 500,
                "body": json.dumps({"reply": "Server error: OPENROUTER_API_KEY is missing in Netlify settings."})
            }

        # System persona prompt
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

        formatted_messages = [{"role": "system", "content": system_prompt}] + messages

        payload = json.dumps({
            "model": "meta-llama/llama-3-8b-instruct:free",
            "messages": formatted_messages
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://your-site.netlify.app",
                "X-Title": "Gyan AI"
            },
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))

            if "error" in res_data:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"reply": "AI Error: " + res_data["error"].get("message", "Unknown error")})
                }

            reply = res_data["choices"][0]["message"]["content"] if res_data.get("choices") else "No response generated."

            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json" },
                "body": json.dumps({"reply": reply})
            }

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {
            "statusCode": e.code,
            "body": json.dumps({"reply": f"API Error: {err_body}"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"reply": f"Server error: {str(e)}"})
        }
