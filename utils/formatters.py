# utils/formatters.py
def format_currency(amount):
    """Formate un montant en devise"""
    return f"{amount:,.2f} DA"

def format_percentage(value):
    """Formate un pourcentage"""
    return f"{value:.1f}%"

def format_date(date_obj):
    """Formate une date"""
    if not date_obj:
        return ""
    return date_obj.strftime("%d/%m/%Y")