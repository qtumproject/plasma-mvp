# QTUM Plasma MVP

A port of Plasma MVP to QTUM. It is based on:

- [Minimum Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426)
- [Omisego Plasma MVP](https://github.com/omisego/plasma-mvp)

ETH RPC compatibility is provided by [Janus](https://github.com/qtumproject/janus)

## Dependencies

Docker is required to run qtumd and the ETH RPC compatibility layer.

Check your Python version:

```
python --version
Python 3.6.5
```

Python 3.5 or above should work. But we recommend that you use [pyenv](https://github.com/pyenv/pyenv), and run version 3.6.5.

Install Python dependencies:

```
python setup.py install
```

# Running QTUM Plasma MVP

A docker image is prepared, which contains qtumd, as well as the ETH RPC compatibility layer.

```
docker run --rm \
    --name qtumportal \
    -v `pwd`:/dapp \
    -p 3889:3889 \
    -p 8545:23889 \
    dcb9/qtumportal
```

- 3889 exposes the original QTUM RPC.
- 8545 exposes the ETH compatible RPC.

Next, setup an alias to access the `qtum-cli` tool:

```
alias qcli='docker exec -it qtumportal qcli'
```

Mine 600 blocks to provide an initial balance for testing:

```
qcli generate 600
```

## Setup Plasma

- Create two Plasma users.
- Deploy the root contracts on QTUM.
- Registering the Plasma users.
- Run the child chain.

### Create Users

We are going to:

- Import private keys.
- Fund users.

The private key for the first user. This user also acts as the admin, used to deploy the Plasma contracts, as well as to submit the child-chain blocks.

```
# Private Key
00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35

# QTUM Address Hex
0x7926223070547D2D15b2eF5e7383E541c338FfE9

# QTUM Address Base58
qUbxboqjBRp96j3La8D1RYkyqx5uQbJPoW

# ETH Address
0x6Fd56E72373a34bA39Bf4167aF82e7A411BFED47
```

Note that ETH and QTUM addresses for the same private key are different, and we need to know both. When getting the signer of a signature, the [ecrecover function returns the address in ETH format](https://github.com/qtumproject/cpp-eth-qtum/issues/27).

The private key for second user (normal Plasma user without admin rights):

```
# Private Key
7826adc1127b8cf34c47b2c7909904109d7fe404be04838e323082981c51340e

# QTUM Address Hex
0x2352be3Db3177F0A07Efbe6DA5857615b8c9901D

# QTUM Address Base58
qLn9vqbr2Gx3TsVR9QyTVB5mrMoh4x43Uf

# ETH Address
0x0CF28703ECc9C7dB28F3d496e41666445b0A4EAF
```

Import these keys, and fund the accounts with 500 QTUM each:

```bash
# Admin User
qcli importprivkey \
    cMbgxCJrTYUqgcmiC1berh5DFrtY1KeU4PXZ6NZxgenniF1mXCRk
docker exec -it qtumportal \
    solar prefund qUbxboqjBRp96j3La8D1RYkyqx5uQbJPoW 50000

# Normal User
qcli importprivkey \
    cRcG1jizfBzHxfwu68aMjhy78CpnzD9gJYZ5ggDbzfYD3EQfGUDZ
docker exec -it qtumportal \
    solar prefund qLn9vqbr2Gx3TsVR9QyTVB5mrMoh4x43Uf 50000
```

## Deploy Plasma Contracts (Root Chain)

We'll use the admin user to create the contracts.

```
make root-chain
```

If successful, the address of the contract is writen to the file `plasma_core/contract_addr.py`:

```
cat plasma_core/contract_addr.py
ADDR="0x2208595067499452580F54668104Ffb1b8755d79"
```

## Registering Users

The original Plasma MVP does not require users to pre-register. But we because of the [ecrecover issue](https://github.com/qtumproject/cpp-eth-qtum/issues/27) mentioned above, the smart contract needs way to associate QTUM address to ETH address.

To register the two users:

```
omg register 0x7926223070547D2D15b2eF5e7383E541c338FfE9 00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35

omg register 0x2352be3Db3177F0A07Efbe6DA5857615b8c9901D 7826adc1127b8cf34c47b2c7909904109d7fe404be04838e323082981c51340e
```

## Run The Child Chain

The root-chain is now ready. Let's start the child-chain, a Python server:

```
make child-chain
```

## Deposit Fund To Plasma

We use the first user (the admin) to deposit 100 QTUM into the Plasma Root Chain:

```
omg deposit 10000000000 0x7926223070547D2D15b2eF5e7383E541c338FfE9

Deposited 10000000000 to 0x7926223070547D2D15b2eF5e7383E541c338FfE9
```

You should see the following log output from the child-chain, when the deposit has been confirmed by the root-chain:

```
apply_deposit AttributeDict({'depositor': '0x6Fd56E72373a34bA39Bf4167aF82e7A411BFED47', 'depositBlock': 1, 'token': '0x0000000000000000000000000000000000000000', 'amount': 10000000000})
```

The deposit created a corresponding UTXO on the side chain. Plasma MVP uses a simplified UTXO, such that there can be two VINs and two VOUTs.

The `omg sendtx` is a bit unfriendly, in that it requires many arguments to create a transaction. We are going to use the deposit UTXO as VIN1, leave VIN2 empty, and create two VOUTs of 50 QTUMs each, one to the receiver, and another as change back to the sender.

```bash
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
```

This transaction occurs on Plasma, and is instanteneus. The admin, however, needs to submit the child chain block's merkle root to the root-chain to publish" a Plasma tx for everyone to see:

```bash
# submit a block with the admin's signing key
omg submitblock \
    00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35
```

The child-chain should output:

```yaml
utxo_id: 1000000000
blknum: 1
from: 0x7926223070547D2D15b2eF5e7383E541c338FfE9
block.merkle.root: a2540bf5fef7c09ab916fabd3607385eba19468e6a6e09fced27400254b6ac9b
len: 32
data: 6bd3991cdfe4d2492b262e178370b74ae7c8eeacc7acb052cd5820e62ac548fa
```

## Withdraw From Chain

To user 2 to withdraw a VOUT from the child chain, it is necessary that user 1 had sent one [confirmation signature](https://ethresear.ch/t/why-do-dont-we-need-two-phase-sends-plus-confirmation/1866/14) for the each VIN in that transaction.

From the `sendtx` above, there are two VOUTs on block 1000.

We withdraw the VOUT designated by `1000 0 0` (block 1000, tx 0, vout 0), which belongs to user 1:

```
omg withdraw \
    1000 0 0 \
    `# Use user1's key to create a confirmation sig` \
    00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35
```

Once a withdraw request is on-chain, we need to wait for a challenge period before it could be finalized. For testing purpses, the challenge period is 30 seconds, so we just wait:

```
sleep 30
```

After the challenge period, call `finalize` to settle all valid exits on chain:

```
omg finalize_exits
```

We should see that because a 500 QTUM UTXO had been exited, the contract balance is now decremented:

```
bash scripts/getbalance.sh
  "balance": 5000000000,
```

If user 2 also want to exit, the process is similar:

```
omg withdraw 1000 0 1 00821d8c8a3627adc68aa4034fea953b2f5da553fab312db3fa274240bd49f35
```

Note that the CLI tool is just for testing purposes. Normally user 2 would not know the private key of user 1, and would instead receive the confirmation signature directly.
