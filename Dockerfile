FROM rust:latest
WORKDIR /usr/src/repo
ENV TERM=xterm
CMD ["watch", "-n", "10", "-t", "echo Running"]