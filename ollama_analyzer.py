import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

# Set console output encoding to utf-8 to handle Unicode characters (e.g. Vietnamese)
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config

OLLAMA_API_URL = config.OLLAMA_API_URL
MODEL_NAME = config.MODEL_NAME

def analyze_text_with_ollama(text: str) -> dict:
    """
    Sends the input text to the local Ollama API to extract/standardize intent 
    using structured JSON schema output.
    """
    from datetime import timedelta
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    day_after_tomorrow = now + timedelta(days=2)
    
    current_time_str = now.strftime("%A, %d/%m/%Y %H:%M:%S")
    
    # Prompt instructing the model to parse standard intent/schedule items
    prompt = f"""
You are supported in extracting schedules.
The current system time is: {current_time_str}.

Context Dates (Use these to resolve relative dates):
- "today" / "hôm nay" / "nay" = {now.strftime("%A, %Y-%m-%d")}
- "tomorrow" / "mai" / "ngày mai" = {tomorrow.strftime("%A, %Y-%m-%d")}
- "the day after tomorrow" / "mốt" / "ngày mốt" / "kia" / "ngày kia" = {day_after_tomorrow.strftime("%A, %Y-%m-%d")}

Read the following message and extract the schedule:
Message: "{text}"

Guidelines:
1. Handle Vietnamese language contexts carefully:
   - "mẹ" is a participant meaning "Mother". "bố", "ba" means "Father".
   - Do NOT confuse the Vietnamese word "Mai" (tomorrow) with the month of May or March. Use the pre-calculated Context Dates above.
2. The message may arrive as a single combined string of "[Sender Name] [Message Content]" (e.g. "Mẹ Mai 10h đi ăn sáng").
   - You must identify that the first word (e.g., "Mẹ") is the sender/participant.
   - The message content is the rest (e.g., "Mai 10h đi ăn sáng").
   - Extract the sender as a participant in "participants" list.
   - Event "summary" should be the message topic (e.g., "Ăn sáng với Mẹ"). Do NOT include the relative day word (like "Mai") in the summary.
   - The "intent" should represent the category of the schedule event (e.g., schedule_meeting, task_reminder, social_gathering). Do NOT set the intent to the sender's name or the raw message.
3. You MUST calculate and output the "datetime" field in YYYY-MM-DDTHH:MM:SS format (e.g., 2026-06-04T10:00:00). Use the pre-calculated Context Dates above.
4. IF THE MESSAGE IS JUST A GENERAL REMINDER (e.g., "remember to work on the project") WITHOUT A SPECIFIC TIME:
   - Please return field "co_lich_hen": false
   - Add field "loai_thong_bao": "nhac_nho_chung"
   - Add field "canh_bao": "Missing specific time"
   - Set "datetime" to an empty string.
5. IF THERE IS A TIME:
   - Please return field "co_lich_hen": true
   - Add field "loai_thong_bao": "lich_hen"
"""

    # JSON Schema definition matching the request
    schema = {
        "type": "object",
        "properties": {
            "co_lich_hen": {
                "type": "boolean",
                "description": "True if there is a specific schedule/time, False otherwise."
            },
            "loai_thong_bao": {
                "type": "string",
                "description": "Use 'lich_hen' if there is a specific time, or 'nhac_nho_chung' if it is a general reminder/deadline."
            },
            "canh_bao": {
                "type": "string",
                "description": "Warning details if co_lich_hen is false, otherwise empty."
            },
            "intent": {
                "type": "string",
                "description": "The general category of user intent (e.g., schedule_meeting, task_reminder, social_gathering, none)"
            },
            "summary": {
                "type": "string",
                "description": "Standardized summary of the event (e.g., 'Ăn sáng với Mẹ')."
            },
            "datetime": {
                "type": "string",
                "description": "ISO 8601 date string (YYYY-MM-DDTHH:MM:SS format). Must be calculated relative to context dates."
            },
            "duration_minutes": {
                "type": "integer",
                "description": "Default duration if applicable, otherwise null."
            },
            "participants": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Any mentioned people or participants."
            }
        },
        "required": ["co_lich_hen", "loai_thong_bao", "intent", "summary", "datetime"]
    }

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": schema,
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_API_URL, 
        data=req_data, 
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            # Ollama returns the generated response inside the "response" key
            parsed_response = json.loads(res_json.get("response", "{}"))
            return parsed_response
    except urllib.error.URLError as e:
        print(f"[Ollama Error] Connection failed. Is Ollama running on localhost? Details: {e}")
        return {"error": "Ollama connection failed", "details": str(e)}
    except json.JSONDecodeError as e:
        print(f"[Ollama Error] Failed to parse output JSON: {e}")
        return {"error": "JSON parse error", "details": str(e)}

if __name__ == "__main__":
    test_input = "Mai 9h họp"
    print(f"Raw Input: '{test_input}'")
    print("Calling local Ollama API (JSON Mode)...")
    
    result = analyze_text_with_ollama(test_input)
    print("\nStandardized JSON Output:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
