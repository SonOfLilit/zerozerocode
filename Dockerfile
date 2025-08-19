FROM rust:latest
WORKDIR /usr/src/repos
ENV TERM=xterm
RUN git config --global --add safe.directory '*'
CMD ["watch", "-n", "10", "-t", "echo Running"]