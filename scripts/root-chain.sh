echo 'ADDR=""' > plasma_core/contract_addr.py

rm -rf contract_data
contractaddr="$(python deployment.py | grep address  |  awk '{print $NF}')"
echo $contractaddr

echo ADDR='"'${contractaddr}'"' > plasma_core/contract_addr.py

make init &>/dev/null
