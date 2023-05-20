from flask import Flask, jsonify, request
import json
import random
import re
import string
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_snlm0e(session):
    resp = session.get(url="https://bard.google.com/", timeout=10)
    if resp.status_code != 200:
        raise Exception("Could not get Google Bard")
    SNlM0e = re.search(r"SNlM0e\":\"(.*?)\"", resp.text).group(1)
    return SNlM0e

def ask_bard(session, message):
    headers = {
        "Host": "bard.google.com",
        "X-Same-Domain": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://bard.google.com",
        "Referer": "https://bard.google.com/",
    }
    _reqid = int("".join(random.choices(string.digits, k=4)))
    conversation_id = ""
    response_id = ""
    choice_id = ""
    session.headers = headers
    SNlM0e = get_snlm0e(session)

    params = {
        "bl": "boq_assistant-bard-web-server_20230514.20_p0",
        "_reqid": str(_reqid),
        "rt": "c",
    }

    message_struct = [
        [message],
        None,
        [conversation_id, response_id, choice_id],
    ]
    data = {
        "f.req": json.dumps([None, json.dumps(message_struct)]),
        "at": SNlM0e,
    }

    resp = session.post(
        "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
        params=params,
        data=data,
        timeout=120,
    )

    chat_data = json.loads(resp.content.splitlines()[3])[0][2]
    if not chat_data:
        return {"content": f"Google Bard encountered an error: {resp.content}."}
    json_chat_data = json.loads(chat_data)
    results = {
        "content": json_chat_data[0][0],
        "conversation_id": json_chat_data[1][0],
        "response_id": json_chat_data[1][1],
        "factualityQueries": json_chat_data[3],
        "textQuery": json_chat_data[2][0] if json_chat_data[2] is not None else "",
        "choices": [{"id": i[0], "content": i[1]} for i in json_chat_data[4]],
    }
    conversation_id = results["conversation_id"]
    response_id = results["response_id"]
    choice_id = results["choices"][0]["id"]
    _reqid += 100000
    return results
@app.route('/ask', methods=['POST'])
def ask_question():
    
    # add id
    session_id = "ADD Your ID"
    session = requests.Session()
    session.cookies.set("__Secure-1PSID", session_id)

    data = request.get_json()
    question = data['question']

    response = ask_bard(session, question)

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
