FROM python:3.7.2

WORKDIR /app

COPY requirements.txt /tmp

# utc -> cts
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r /tmp/requirements.txt

COPY src /app

CMD gunicorn -w 2 apis.wsgi
