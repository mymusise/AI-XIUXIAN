from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.serializers import Serializer
from utils.exceptions import GenericExceptionMixin
from apis.settings import DEBUG

import logging


class BaseView(GenericExceptionMixin, GenericAPIView):
    logger = logging.getLogger('apis')
    aliyun_logger = logging.getLogger('aliyun')
    need_print_logger = True
    input_serializer = {
        'GET': None,
        'POST': None,
        'PUT': None,
        'DELETE': None
    }
    # need authentication
    _ignore_model_permissions = False

    def print_logger(self, request):
        parameters = getattr(request, request.method, {})
        if not parameters:
            parameters = getattr(request, 'data', {})
        if not parameters:
            parameters = {}
        parameters_string = ''
        for key, value in parameters.items():
            parameters_string += '[%s=%s] ' % (key, value)
        for key, value in self.kwargs.items():
            parameters_string += '[%s=%s] ' % (key, value)
        if request.user:
            user_id = request.user.id
        else:
            user_id = 0
        self.logger.info("[%s_%s_request] with parameters [user_id=%s] %s" % (
            self.__class__.__name__,
            request.method,
            user_id,
            parameters_string
        ))

    def initial_serializer_data(self, request):
        parameters = getattr(request, request.method, {})
        if not parameters:
            parameters = getattr(request, 'data', {})
        if not parameters:
            parameters = {}
        serializer = self.input_serializer.get(request.method)(data=parameters)
        if not serializer.is_valid():
            message = serializer.errors
            log = f"[{self.__class__.__name__}_parameter_error]"
            log = f"{log} [params={parameters}] {serializer.errors}"
            self.logger.info(log)
            raise self.invalid_params(msg=message)
        request.serializer = serializer

    def dispatch(self, request, *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.
        """
        self.args = args
        self.kwargs = kwargs
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:

            self.initial(request, *args, **kwargs)
            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            if self.need_print_logger:
                self.print_logger(request)
            if self.input_serializer.get(request.method):
                self.initial_serializer_data(request)

            response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(
            request, response, *args, **kwargs)
        return self.response

    def success(self, data={}):
        return Response(data)


class BaseSerializer(Serializer):

    @property
    def errors(self):
        ret = super(BaseSerializer, self).errors
        _errors = []
        for key, error_list in ret.items():
            for error in error_list:
                if error.code == "required":
                    msg = f"缺少参数{key}"
                elif error.code == "invalid":
                    msg = f"{key}的格式不对"
                elif error.code == "blank":
                    msg = f"{key}不能为空"
                else:
                    msg = error.title()
                _errors.append(msg)
        return " \n ".join(_errors)