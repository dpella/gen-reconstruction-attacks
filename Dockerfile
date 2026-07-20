FROM python:3.12.3

WORKDIR /workspace

# System dependencies: GLPK for the MIP solver, plus common build tools
# some pip wheels need.
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

# Install only the tool dependencies at build time. The heavier
# privacy-metrics dependencies (anonymeter, synthcity, PyTorch, ...)
# live in requirements-eval.txt and are installed on demand via
# scripts/install_eval_deps.sh — see the README.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source tree (harmless in the devcontainer, where the
# workspace is bind-mounted over this at runtime).
COPY . .

CMD ["bash"]
