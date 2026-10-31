from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
import os

def health_check(request):
    """
    Health check endpoint returning system, database and cache connectivity status.
    """
    health_status = {
        'status': 'healthy',
        'service': 'securflow-backend',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'components': {
            'database': 'unknown',
            'redis': 'unknown',
        }
    }
    
    # Check Database
    try:
        connection.ensure_connection()
        health_status['components']['database'] = 'connected'
    except Exception as e:
        health_status['components']['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'

    # Check Redis
    redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    try:
        import redis
        r = redis.from_url(redis_url, socket_timeout=1)
        r.ping()
        health_status['components']['redis'] = 'connected'
    except Exception as e:
        health_status['components']['redis'] = f'disconnected ({str(e)})'
        # Redis optional for basic API liveness
        if health_status['status'] == 'healthy':
            health_status['status'] = 'healthy_with_warnings'

    status_code = 200 if health_status['status'] in ('healthy', 'healthy_with_warnings') else 503
    return JsonResponse(health_status, status=status_code)
