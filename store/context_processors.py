from store.models import ExchangeRate

def bcv_context(request):
    currency = request.session.get('currency', 'USD')
    try:
        bcv_rate = ExchangeRate.objects.get(currency='USD')
        rate = bcv_rate.rate
    except ExchangeRate.DoesNotExist:
        rate = 0
    
    return {
        'current_currency': currency,
        'current_bcv_rate': rate,
    }
