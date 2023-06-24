import circleci.analytics_clj.core as a
from mount import de state
from environ import env
from clojure.tools.logging import log

@de state('analytics', 'start')
def initialize(segment_key):
    try:
        return a.initialize(segment_key)
    except Exception as e:
        log.warnf("failed to initialize analytics: %s", e.getMessage())
        return None

def track(context, event, traits):
    analytics = analytics or initialize(env['segment_key'])
    email = context['customer']['email']
    a.track(analytics, email, event, traits)

def identify(context):
    analytics = analytics or initialize(env['segment_key'])
    email = context['customer']['email']
    a.identify(analytics, email, {'email': email})