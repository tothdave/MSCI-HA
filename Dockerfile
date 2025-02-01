FROM python:3.12.8-slim-bookworm

RUN apt-get update && apt-get install -y \
    gcc python3-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash msci-user

WORKDIR /home/msci-user

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ip_tool.py ./

RUN mkdir -p /home/msci-user/results && chown -R msci-user:msci-user /home/msci-user/results

USER msci-user

ENTRYPOINT ["python", "ip_tool.py"]
