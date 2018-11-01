set -e

echo 'Register User1 (Admin)'
omg register 0x7926223070547D2D15b2eF5e7383E541c338FfE9 00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35
echo '####################################'

echo 'Register User2'
omg register 0x2352be3Db3177F0A07Efbe6DA5857615b8c9901D 7826adc1127b8cf34c47b2c7909904109d7fe404be04838e323082981c51340e
echo '####################################'

echo 'User1 deposits 1000 QTUM to root chain'
omg deposit 10000000000 0x7926223070547D2D15b2eF5e7383E541c338FfE9
echo '####################################'

echo 'User1 sends 500 QTUM to User2'
omg sendtx \
    `# vin 1 (blknum, txindex, oindex)` \
    1 0 0 \
    `# vin 2 (blknum, txindex, oindex)` \
    0 0 0 \
    `# The type of the (ERC20) token. 0x0 is the "native" token, which is ETH or QTUM.` \
    0x0 \
    `# vout 1` \
    0x7926223070547D2D15b2eF5e7383E541c338FfE9 5000000000 \
    `# vout 1` \
    0x2352be3Db3177F0A07Efbe6DA5857615b8c9901D 5000000000 \
    `# Signing key of sender` \
    00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35
echo '####################################'

echo 'Operator submits block to root chain'
omg submitblock \
    00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35
echo '####################################'

echo 'exit user1'
omg withdraw 1000 0 0 00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35

echo 'wait 30 seconds to finalize exit'
sleep 30 && omg finalize_exits 0x7926223070547D2D15b2eF5e7383E541c338FfE9

echo 'get root chain balance'
bash scripts/getbalance.sh
echo '####################################'

echo 'exit user2'
omg withdraw 1000 0 1 00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35

echo 'wait 30 seconds to finalize exit'
sleep 30 && omg finalize_exits 0x7926223070547D2D15b2eF5e7383E541c338FfE9

echo 'get root chain balance'
bash scripts/getbalance.sh
