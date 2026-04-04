import requests
import json
import re

prompt = "You are a Portfolio Manager. Distribute $3600. Output strictly a JSON array: [{\"symbol\": \"MSFT\", \"action\": \"BUY\", \"percentage\": 10, \"reasoning\": \"good\"}]"

try:
    print("Calling Ollama...")
    res = requests.post('http://127.0.0.1:11434/api/generate', json={'model': 'deepseek-r1', 'prompt': prompt, 'stream': False}, timeout=120)
    response_text = res.json().get('response', '[]')
    print('RAW RESPONSE:')
    print(response_text)

    clean_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
    print('\nCLEAN TEXT:')
    print(clean_text)

    array_match = re.search(r'\[.*\]', clean_text, flags=re.DOTALL)
    if array_match:
        try:
            data = json.loads(array_match.group(0))
            print('\nPARSED ARRAY:', data)
        except Exception as e:
            print('\nJSON ERROR:', e)
            print('Extracted string was:', array_match.group(0))
    else:
        print('\nNO ARRAY MATCH FOUND')
except Exception as e:
    print('REQUEST ERROR:', e)
