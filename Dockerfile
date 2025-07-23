FROM rust:latest
WORKDIR /usr/src/repo
ENV TERM=xterm
RUN git config --global --add safe.directory /usr/src/repo
CMD ["watch", "-n", "10", "-t", "echo Running"]