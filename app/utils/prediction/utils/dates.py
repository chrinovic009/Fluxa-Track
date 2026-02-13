from datetime import date, timedelta

def get_current_period():
    today = date.today()
    start = today - timedelta(days=30)
    end = today
    return start, end
