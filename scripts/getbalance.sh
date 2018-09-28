alias qcli='qtum-cli -rpcport=3889 -rpcuser=qtum -rpcpassword=test -regtest'

contractAddr=$(grep 'ADDR' plasma_core/contract_addr.py | awk -F '"' '{print $2}')
contractAddr=${contractAddr:2}

qcli getaccountinfo $contractAddr | grep balance
