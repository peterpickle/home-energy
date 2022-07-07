from django.conf import settings

def feature_flags(request):
    # return the value (s) you want as a dictionnary.
    return {
            'FEATURE_CONSUMPTION': settings.FEATURE_CONSUMPTION,
            'FEATURE_GAS': settings.FEATURE_GAS,
            'FEATURE_PRODUCTION': settings.FEATURE_PRODUCTION,
            }
