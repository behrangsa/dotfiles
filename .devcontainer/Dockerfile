FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install essential development tools
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        curl \
        wget \
        gnupg \
        lsb-release \
        ca-certificates \
        apt-transport-https \
        software-properties-common \
        git-core \
        zsh \
        vim \
        nano \
        htop \
        tree \
        bash-completion \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
    && apt-get autoremove -y && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set locale
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Configure git
RUN git config --system core.editor "vim" \
    && git config --system credential.helper "cache --timeout=3600" \
    && git config --system pull.rebase false

# Set up timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone