from datetime import datetime

def humanize_date(date):
    if not isinstance(date, datetime):
        return "—"
    delta = (datetime.utcnow().date() - date.date()).days

    now = datetime.utcnow()
    diff = now - date
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return f"il y a {seconds} secondes"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif delta == 0:
        return "Aujourd’hui"
    elif delta == 1:
        return "Hier"
    elif delta > 1 and delta < 7:
        return f"il y a {delta} jours"
    else:
        return date.strftime('%d %B %Y')