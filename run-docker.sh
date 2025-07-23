#!/bin/sh
docker build -t zerozerocode .
docker stop zerozerocode && docker rm zerozerocode
docker run --detach --name zerozerocode --volume `realpath ./gitrepo`:/usr/src/repo zerozerocode
