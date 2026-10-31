"""
Consistent government-grade API error response handler for SecurFlow.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            "success": False,
            "error": {
                "status_code": response.status_code,
                "message": "An error occurred while processing the request.",
                "details": response.data
            }
        }
        # Provide human-readable message if detail or message exists
        if isinstance(response.data, dict):
            if "detail" in response.data:
                custom_data["error"]["message"] = str(response.data["detail"])
            elif "message" in response.data:
                custom_data["error"]["message"] = str(response.data["message"])
        elif isinstance(response.data, list) and len(response.data) > 0:
            custom_data["error"]["message"] = str(response.data[0])

        response.data = custom_data

    return response
