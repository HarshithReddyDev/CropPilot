FROM postgis/postgis:16-3.4

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      postgresql-16-pgvector \
      build-essential \
      cmake \
      git \
      postgresql-server-dev-16 \
      ca-certificates && \
    git clone --depth 1 https://github.com/zachasme/h3-pg.git /tmp/h3-pg && \
    cd /tmp/h3-pg && \
    make && \
    make install && \
    rm -rf /tmp/h3-pg && \
    apt-get purge -y --auto-remove build-essential cmake git postgresql-server-dev-16 ca-certificates && \
    rm -rf /var/lib/apt/lists/*
