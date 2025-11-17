from datetime import datetime

def init(manager=None):
    # optional initialization hook
    pass

def handle(request):
    text = ""
    if isinstance(request, dict):
        text = request.get("text", "")
    else:
        text = str(request)
    q = text.lower()
    if "date" in q or "time" in q or "today" in q:
        now = datetime.now()
        return {
            "plugin": "time_master",
            "response": now.strftime("%A, %B %d, %Y"),
            "timestamp": now.isoformat()
        }
    return None
