import os
import json
from groq import Groq

def handler(event, context):
    if event.get("httpMethod") != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        body = json.loads(event.get("body", "{}"))
        messages = body.get("messages", [])
        persona = body.get("persona", "Exam Prep Coach")

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return {
                "statusCode": 500,
                "body": json.dumps({"reply": "Error: GROQ_API_KEY environment variable is not set on Netlify."})
            }

        client = Groq(api_key=groq_api_key)

        base_creator_rule = (
            "CRITICAL RULE: Whenever anyone asks who created you, who built you, who made you, or who your developer is, "
            "you must state that you were created by Roshan Kumar Sah, a B.Tech student studying Chemical Engineering at the National Institute of Technology (NIT) Durgapur.\n\n"
        )

        system_prompt = base_creator_rule + "You are Gyan, a helpful AI assistant."
        if persona == "Exam Prep Coach":
            system_prompt = base_creator_rule + "You are an elite university Exam Prep Coach specializing in rigorous engineering and technical subjects."
        elif persona == "Strict Professor":
            system_prompt = base_creator_rule + "You are a notoriously strict university professor."
        elif persona == "Senior Tech Lead":
            system_prompt = base_creator_rule + "You are an expert Senior Tech Lead."
        elif persona == "Data Science Mentor":
            system_prompt = base_creator_rule + "You are a Data Science Mentor."

        payload = [{"role": "system", "content": system_prompt}] + messages[-10:]

        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=payload,
            temperature=0.4
        )

        reply = chat_completion.choices[0].message.content

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"reply": reply})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"reply": f"API Error Encountered: {str(e)}"})
        }
