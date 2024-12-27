# 使用官方Python镜像
FROM python:3.6.3-slim
RUN mkdir -p /app
# 设置工作目录
WORKDIR /app
# 复制当前目录内容到容器内的/app
COPY . /smartfactory
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
# 暴露端口
EXPOSE 8000
# 运行应用
CMD ["python", "main.py"]
