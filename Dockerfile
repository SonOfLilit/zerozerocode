FROM rust:latest
WORKDIR /usr/src/repo
ENV TERM=xterm
RUN apt update && \
    apt install -y --no-install-recommends ed && \
    rm -rf /var/lib/apt/lists/*
RUN git config --global --add safe.directory /usr/src/repo
CMD ["watch", "-n", "10", "-t", "echo Running"]