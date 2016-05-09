#!/bin/sh

echo "Installing RO manageDB dependencies..."

SUDO=`which sudo`
APT="python-pip mongodb-server python-lxml python-m2crypto python-openssl python-dateutil xmlsec1 libxmlsec1-dev autoconf-archive automake g++ git-core libtool python-dev swig"
$SUDO apt-get install -y ${APT}

PIP=`which pip`
$SUDO $PIP install -r pip_dependencies

echo "Installing RO manageDB dependencies... Done"
