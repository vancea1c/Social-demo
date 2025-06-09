from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import connections
from django.db.utils import OperationalError

@require_GET
def health_check(request):
    db_conn = connections["default"]
    try:
        db_conn.cursor()
    except OperationalError:
        return JsonResponse({"status": "error", "db": "unreachable"}, status=503)
    return JsonResponse({"status": "ok"})
