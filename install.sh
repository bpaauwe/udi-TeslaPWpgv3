#!/usr/bin/env bash


mkdir -p profile 
mkdir -p profile/nodedef
mkdir -p profile/nls
mkdir -p profile/editor


rf=requirements.txt
if [ -f /usr/local/etc/pkg/repos/udi.conf ]; then
  rf=requirements_polisy.txt
  pip install git+https://github.com/jrester/tesla_powerwall#egg=tesla_powerwall
fi
echo "Using: $rf"
if ! pip3 install -r $rf --user; then
  echo "ERROR: pip3 failed, see above"
  exit 1
fi

pip install --upgrade pip

pip install -r requirements.txt --user