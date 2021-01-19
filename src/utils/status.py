class Status:
    SUCCESS = 0  # 成功
    NEED_LOGIN = 1  # 需要登录
    INVALID_PARAMS = 2  # 参数错误
    INTERNAL_ERROR = 3  # 系统内部错误
    NOT_EXIST = 4  # 请求对象不存在
    ASYNC_WAIT = 5  # 需要等待
    ILLEGAL_OPERATION = 6  # 非法操作
    OUTCALL_ERROR = 7  # 外部调用失败
