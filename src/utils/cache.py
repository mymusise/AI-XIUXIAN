from django.core.cache import cache


def cache_params(variable):
    timeout = 210

    def params_warpper(func):
        def func_warpper(*args, **kwargs):
            key = f"{func.__module__}.{func.__qualname__}__"
            if '.' in func.__qualname__:
                params = args[1:]
            else:
                params = args
            key += "__".join([str(p) for p in params])
            if kwargs:
                key += "_kwargs_"
                key += "__".join([f"{k}_{v}" for k, v in kwargs.items()])
            _cache_content = cache.get(key)
            if not _cache_content:
                result = func(*args, **kwargs)
                cache.set(key, result, timeout)
                return result
            return _cache_content
        return func_warpper
    if callable(variable):
        function = variable
        return params_warpper(function)
    timeout = variable
    return params_warpper
