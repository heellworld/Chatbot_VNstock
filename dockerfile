FROM apache/airflow:2.10.5

# Sao chép requirements.txt vào container
COPY requirements.txt /tmp/requirements.txt

# Cài đặt các gói phụ thuộc hệ thống
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Chuyển về user airflow để cài đặt các package từ requirements.txt
USER airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt