FROM python:3.12.8-slim-bookworm

RUN apt-get update && apt-get install -y \
    gcc python3-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1001 msci-group && \
    useradd -ms /bin/bash --uid 1001 --gid 1001 msci-user

WORKDIR /home/msci-user

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ip_tool.py ./

# For local docker testing only
# RUN mkdir -p /home/msci-user/ip-tool-data && chown -R msci-user:msci-user /home/msci-user/ip-tool-data

USER msci-user

ENTRYPOINT ["python", "ip_tool.py"]
