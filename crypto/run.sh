#!/usr/bin/env sh

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Check if the necessary dependencies are available


if ! command -v dpkg >/dev/null 2>&1; then
    echo "dpkg command is not available, but it's needed. Terminating..."
    exit 1
fi

if ! command -v dpkg-query >/dev/null 2>&1; then
    echo "dpkg-query command is not available, but it's needed. Terminating..."
    exit 1
fi

if ! dpkg-query -W python3-cryptoauthlib >/dev/null 2>&1; then
    echo "python3-cryptoauthlib is not available, to install run"
    echo 'echo "deb https://packages.cloud.google.com/apt coral-cloud-stable main" | sudo tee /etc/apt/sources.list.d/coral-cloud.list'
    echo "curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -"
    echo "sudo apt update"
    echo "sudo apt install python3-coral-cloudiot"
    exit 1
fi

#setting the CRYPTO_AUTH_LIB_SHARED_OBJECT environment variable that points to the crytoauthlib shared object file.
export CRYPTO_AUTH_LIB_SHARED_OBJECT=$(dpkg -L python3-cryptoauthlib | grep -i .so)
export CRYPTO_AUTH_LIB_DIR=$(dirname "${CRYPTO_AUTH_LIB_SHARED_OBJECT}")
export CRYPTO_AUTH_LIB_NAME=$(basename "${CRYPTO_AUTH_LIB_SHARED_OBJECT}")
export CRYPTO_AUTH_LIB_NAME=${CRYPTO_AUTH_LIB_NAME#lib}
export CRYPTO_AUTH_LIB_NAME=${CRYPTO_AUTH_LIB_NAME%.*}
export CGO_LDFLAGS="-L${CRYPTO_AUTH_LIB_DIR} -l${CRYPTO_AUTH_LIB_NAME}"

#set current folder to GOPATH
export GOPATH="$GOPATH:$(pwd)"

#run test
LD_PRELOAD=${CRYPTO_AUTH_LIB_SHARED_OBJECT} go run src/test/testing.go