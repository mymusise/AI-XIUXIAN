import logging
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import set_rollback
from .status import Status


error_logger = logging.getLogger('exception')


def res_content(status, msg, data={}):
    return {'message': msg, 'data': data}


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if exc.status_code == 403:
            data = res_content(Status.NEED_LOGIN, "need login")
        else:
            data = res_content(Status.INTERNAL_ERROR, exc.detail)

        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
        data = res_content(Status.NOT_EXIST, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
        data = res_content(Status.ILLEGAL_OPERATION, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, NeedLoginException):
        data = res_content(Status.NEED_LOGIN, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_403_FORBIDDEN)

    elif isinstance(exc, ObjectNotExitException):
        data = res_content(Status.NOT_EXIST, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, InvalidParamsException):
        data = res_content(Status.INVALID_PARAMS, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    elif isinstance(exc, InternalErrorException):
        data = res_content(Status.INTERNAL_ERROR, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif isinstance(exc, AsyncWaitException):
        data = res_content(Status.ASYNC_WAIT, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_408_REQUEST_TIMEOUT)

    elif isinstance(exc, IllegalOperationException):
        data = res_content(Status.ILLEGAL_OPERATION, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    elif isinstance(exc, OutCallException):
        data = res_content(Status.OUTCALL_ERROR, str(exc))
        set_rollback()
        return Response(data, status=status.HTTP_504_GATEWAY_TIMEOUT)

    error_logger.exception("[system error]")
    data = res_content(500, "系统错误")
    return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NeedLoginException(Exception):
    pass


class ObjectNotExitException(Exception):
    pass


class InvalidParamsException(Exception):
    pass


class InternalErrorException(Exception):
    pass


class AsyncWaitException(Exception):
    pass


class IllegalOperationException(Exception):
    pass


class OutCallException(Exception):
    pass


class GenericExceptionMixin:

    def need_login(self, msg='不登录你也敢进来'):
        raise NeedLoginException(msg)

    def object_not_exit(self, msg=''):
        raise ObjectNotExitException(msg)

    def invalid_params(self, msg=''):
        raise InvalidParamsException(msg)

    def internal_error(self, msg=''):
        raise InternalErrorException(msg)

    def illegal_operation(self, msg='非法操作'):
        raise IllegalOperationException(msg)
