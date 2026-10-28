FROM rust:1.85-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-dev gcc libc6-dev ca-certificates && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/build && /opt/build/bin/pip install --no-cache-dir pip==24.3.1 maturin==1.7.8
ENV PATH="/opt/build/bin:/usr/local/cargo/bin:${PATH}"
COPY base /source/base
COPY head /source/head
RUN mkdir -p /wheels/base /wheels/head /wheels/test && \
    python -m pip wheel --no-deps --no-build-isolation /source/base -w /wheels/base && \
    python -m pip wheel --no-deps --no-build-isolation /source/head -w /wheels/head && \
    python -m pip download --only-binary=:all: pytest==8.3.5 -d /wheels/test
RUN python3 -m venv /opt/base && python3 -m venv /opt/head && \
    /opt/base/bin/pip install --no-index --no-deps /wheels/base/*.whl && \
    /opt/head/bin/pip install --no-index --no-deps /wheels/head/*.whl && \
    /opt/head/bin/pip install --no-index --find-links=/wheels/test pytest==8.3.5 && \
    cp /source/head/properr/__init__.py /opt/original.py && \
    cmp /source/head/tests/test_import.py /source/base/tests/test_import.py
WORKDIR /work
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65534:65534
