FROM python:3.12.3

WORKDIR /workspace

# System dependencies (GLPK for the MIP solver, plus common build tools
# needed by some pip wheels).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       wget \
       git \
       build-essential \
       glpk-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Copy just the requirements first for better Docker layer caching.
COPY requirements.txt requirements-eval.txt ./

# Install the tool dependencies (small) and the evaluation dependencies
# (larger — pulls in torch, synthcity, sklearn, pandas).
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-eval.txt

# Copy the source tree.
COPY . .

CMD ["bash"]
