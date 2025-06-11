import requests
from flask import Flask, request, jsonify, render_template
import openai
import json

app = Flask(__name__)

# Data model (simulating your DB)
AI_SOURCE = {
    'chatgpt': { 'name': 'chatgpt' },
    'deepseek': { 'name': 'deepseek' }
}

API_VERSIONS = {
    'gpt-4.0': { 'ai_source': 'chatgpt', 'name': 'gpt-4.0' },
    'deepseek/deepseek-r1-0528:free': { 'ai_source': 'deepseek', 'name': 'deepseek/deepseek-r1-0528:free' }
}

SETUP = {
    'api_key': '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',
    'ai_version': 'deepseek/deepseek-r1-0528:free'
}

PROCESSES = {
    'meeting_minutes_maker': {
        'process_name': 'meeting_minutes_maker',
        'ai_source': 'deepseek',
        'ai_version': 'deepseek/deepseek-r1-0528:free',
        'prompt_order': ['system']
    },
    'formal_email_genrator': {
        'process_name': 'formal_email_genrator',
        'ai_source': 'deepseek',
        'ai_version': 'deepseek/deepseek-r1-0528:free',
        'prompt_order': ['system']
    }
}

PROMPTS = [
    {
        'process': 'meeting_minutes_maker',
        'role': 'system',
        'prompt': 'You are meeting minutes maker based on the provided content. Always give a short 2 minutes meeting overview.'
    },
    {
        'process': 'formal_email_genrator',
        'role': 'system',
        'prompt': 'You are a formal email generator. Always generate a professional email based on the provided content. my name is Subash. CEO of Doumein, Contact: 6382476871'
    }
]

# Setup OpenAI API key (used only for chatgpt)
openai.api_key = SETUP['api_key']

@app.route('/', methods=['GET'])
def index():
    process_list = list(PROCESSES.keys())
    return render_template('index.html', processes=process_list)

@app.route('/ask', methods=['POST'])
def ask():
    print("\n===== New /ask request =====")
    
    data = request.json
    print(f"[DEBUG] Received data: {data}")

    process_name = data['process']
    user_query = data['query']

    print(f"[DEBUG] Selected process: {process_name}")
    print(f"[DEBUG] User query: {user_query}")

    # Step 1 - Lookup Process
    process = PROCESSES.get(process_name)
    if not process:
        print("[ERROR] Invalid process selected.")
        return jsonify({'response': 'Invalid process selected.'})

    ai_source = process['ai_source']
    ai_version = process['ai_version']
    prompt_order = process['prompt_order']

    print(f"[DEBUG] AI Source: {ai_source}, AI Version: {ai_version}")
    print(f"[DEBUG] Prompt Order: {prompt_order}")

    # Step 2 - Build messages based on Prompt_Order and Prompts
    messages = []

    for role in prompt_order:
        # Find matching prompt
        matching_prompt = next((p for p in PROMPTS if p['process'] == process_name and p['role'] == role), None)
        if matching_prompt:
            messages.append({ 'role': role, 'content': matching_prompt['prompt'] })
            print(f"[DEBUG] Added message for role '{role}': {matching_prompt['prompt']}")
        else:
            print(f"[WARNING] No matching prompt found for role '{role}' in process '{process_name}'")

    # Step 3 - Add User message
    messages.append({ 'role': 'user', 'content': user_query })
    print(f"[DEBUG] Added user message: {user_query}")

    # Step 4 - Call AI API (dynamic based on ai_source)
    try:
        if ai_source == 'chatgpt':
            print("[DEBUG] Calling OpenAI ChatCompletion API...")
            response = openai.ChatCompletion.create(
                model=ai_version,
                messages=messages
            )
            reply = response['choices'][0]['message']['content'].strip()
            print("[DEBUG] Received reply from ChatGPT.")

        elif ai_source == 'deepseek':
            print("[DEBUG] Calling OpenRouter API for DeepSeek...")
            correction_response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {SETUP['api_key']}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": ai_version,
                    "messages": messages,
                    "temperature": 0.1
                })
            )
            reply = correction_response.json()['choices'][0]['message']['content'].strip()
            print("[DEBUG] Received reply from DeepSeek.")

        else:
            reply = 'Error: Unsupported AI source.'
            print("[ERROR] Unsupported AI source selected.")

    except Exception as e:
        reply = f'Error calling AI: {str(e)}'
        print(f"[ERROR] Exception occurred: {str(e)}")

    print(f"[DEBUG] Final reply: {reply}")

    # Return
    return jsonify({ 'response': reply })

if __name__ == '__main__':
    app.run(debug=True)
