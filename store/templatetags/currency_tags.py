from django import template

register = template.Library()

@register.filter
def format_price(value, request=None):
    """
    Format price based on the selected currency in the session.
    value should be in USD.
    """
    if not value:
        return ""
        
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    if request:
        currency = request.session.get('currency', 'USD')
        if currency == 'VES':
            from store.models import ExchangeRate
            try:
                bcv_rate = ExchangeRate.objects.get(currency='USD').rate
                bs_value = value * float(bcv_rate)
                return f"Bs. {bs_value:,.2f}"
            except ExchangeRate.DoesNotExist:
                return f"Bs. {value:,.2f} (Sin tasa)"
                
    return f"${value:,.2f}"

@register.filter
def to_bs(value, rate):
    """
    Convert USD value to VES using the provided rate.
    """
    if not value or not rate:
        return "Bs. 0.00"
        
    try:
        value = float(value)
        rate = float(rate)
        bs_value = value * rate
        return f"Bs. {bs_value:,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def format_price_usd(value):
    """Always format price in USD regardless of session currency."""
    if not value:
        return ""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    return f"${value:,.2f}"

@register.filter
def format_price_bs(value):
    """Always format price in Bs. using the current BCV rate."""
    if not value:
        return ""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    from store.models import ExchangeRate
    try:
        bcv_rate = ExchangeRate.objects.get(currency='USD').rate
        bs_value = value * float(bcv_rate)
        return f"Bs. {bs_value:,.2f}"
    except ExchangeRate.DoesNotExist:
        return f"Bs. {value:,.2f} (Sin tasa)"
