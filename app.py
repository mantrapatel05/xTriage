from flask import Flask, request, jsonify
from triage.summarizer import summarize_issue
from triage.priority import classify_priority
from triage.router import route_bug

app = Flask(__name__)

@app.route('/')
def home():
    return "Bug Triage System is running."

@app.route('/triage', methods=['POST'])
def triage_bug():
    bug = request.get_json()

    if not bug:
        return jsonify({"error": "No bug data provided"}), 400
    
    summary = summarize_issue(bug)
    priority_level, reasons, confidence = classify_priority(bug)
    team = route_bug(bug)

    response = {
        "summary": summary,
        "priority": priority_level,
        "assigned_team": team,
        "confidence" : confidence,
        "reasons": reasons
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
