import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that:
    - Normalises all error responses to {"error": "...", "detail": ...}
    - Logs unexpected exceptions
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': True,
            'status_code': response.status_code,
        }

        if isinstance(response.data, dict):
            detail = response.data.get('detail', response.data)
        else:
            detail = response.data

        error_data['detail'] = detail
        response.data = error_data
        return response

    # Unhandled exception — log and return 500
    logger.exception('Unhandled exception in view: %s', exc)
    return Response(
        {
            'error': True,
            'status_code': 500,
            'detail': 'An unexpected error occurred. Please try again.',
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
