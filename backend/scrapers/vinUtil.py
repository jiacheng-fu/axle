from datetime import datetime

def calculate_age(year):
    if not year:
        return None
    return datetime.now().year - int(year)
