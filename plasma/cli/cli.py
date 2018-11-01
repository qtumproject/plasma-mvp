import click
from ethereum import utils
from plasma_core.constants import NULL_ADDRESS
from plasma_core.transaction import Transaction
from plasma_core.utils.utils import confirm_tx
from plasma.client.client import Client
from plasma.client.exceptions import ChildChainServiceError
from plasma_core.utils.address import address_to_hex


CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    ctx.obj = Client()


def client_call(fn, argz=(), successmessage=""):
    try:
        output = fn(*argz)
        if successmessage:
            print(successmessage)
        return output
    except ChildChainServiceError as err:
        print("Error:", err)
        print("additional details can be found from the child chain's server output")


@cli.command()
@click.argument('amount', required=True, type=int)
@click.argument('address', required=True)
@click.pass_obj
def deposit(client, amount, address):
    client.deposit(amount, address)
    print("Deposited {0} to {1}".format(amount, address))


@cli.command()
@click.argument('blknum1', type=int)
@click.argument('txindex1', type=int)
@click.argument('oindex1', type=int)
@click.argument('blknum2', type=int)
@click.argument('txindex2', type=int)
@click.argument('oindex2', type=int)
@click.argument('cur12', default="0x0")
@click.argument('newowner1')
@click.argument('amount1', type=int)
@click.argument('newowner2')
@click.argument('amount2', type=int)
@click.argument('key1')
@click.argument('key2', required=False)
@click.pass_obj
def sendtx(client,
           blknum1, txindex1, oindex1,
           blknum2, txindex2, oindex2,
           cur12,
           amount1, newowner1,
           amount2, newowner2,
           key1, key2):
    if cur12 == "0x0":
        cur12 = NULL_ADDRESS
    if newowner1 == "0x0":
        newowner1 = NULL_ADDRESS
    if newowner2 == "0x0":
        newowner2 = NULL_ADDRESS

    # Form a transaction
    tx = Transaction(blknum1, txindex1, oindex1,
                     blknum2, txindex2, oindex2,
                     utils.normalize_address(cur12),
                     utils.normalize_address(newowner1), amount1,
                     utils.normalize_address(newowner2), amount2)

    # Sign it
    if key1:
        tx.sign1(utils.normalize_key(key1))
    if key2:
        tx.sign2(utils.normalize_key(key2))

    print("key1:", key1)
    print("sender1:", address_to_hex(tx.sender1))

    client_call(client.apply_transaction, [tx], "Sent transaction")

@cli.command()
@click.argument('key', required=True)
@click.pass_obj
def submitblock(client, key):

    # Get the current block, already decoded by client
    block = client_call(client.get_current_block)

    # Sign the block
    block.make_mutable()
    normalized_key = utils.normalize_key(key)
    block.sign(normalized_key)

    client_call(client.submit_block, [block], "Submitted current block")


@cli.command()
@click.argument('blknum', required=True, type=int)
@click.argument('txindex', required=True, type=int)
@click.argument('oindex', required=True, type=int)
@click.argument('key1')
@click.argument('key2', required=False)
@click.pass_obj
def withdraw(client,
             blknum, txindex, oindex,
             key1, key2):

    # Get the transaction's block, already decoded by client
    block = client_call(client.get_block, [blknum])

    # Create a Merkle proof
    tx = block.transaction_set[txindex]
    proof = block.merkle.create_membership_proof(tx.merkle_hash)

    # Create the confirmation signatures
    confirmSig1, confirmSig2 = b'', b''
    if key1:
        confirmSig1 = confirm_tx(tx, block.merkle.root, utils.normalize_key(key1))
    if key2:
        confirmSig2 = confirm_tx(tx, block.merkle.root, utils.normalize_key(key2))
    sigs = tx.sig1 + tx.sig2 + confirmSig1 + confirmSig2

    client.withdraw(blknum, txindex, oindex, tx, proof, sigs)
    print("Submitted withdrawal")


@cli.command()
@click.argument('owner', required=True)
@click.argument('blknum', required=True, type=int)
@click.argument('amount', required=True, type=int)
@click.pass_obj
def withdrawdeposit(client, owner, blknum, amount):
    deposit_pos = blknum * 1000000000
    client.withdraw_deposit(owner, deposit_pos, amount)
    print("Submitted withdrawal")

@cli.command()
@click.argument('account', required=True)
@click.pass_obj
def finalize_exits(client, account):
    client.finalize_exits(account)
    print("Submitted finalizeExits")

@cli.command()
@click.argument('blknum', required=True, type=int)
@click.argument('key', required=True)
@click.pass_obj
def confirm_sig(client, blknum, key):
    utxo_id = blknum * 1000000000 + 10000 * 0 + 0

    block = client_call(client.get_block, [blknum])
    root = block.root
    print("block root:", root)

    tx = client_call(client.get_transaction, [utxo_id])

    _key = utils.normalize_key(key)

    confirmSig = confirm_tx(tx, root, _key)

    print("confirm sig:", utils.encode_hex(confirmSig))

@cli.command()
@click.argument('blknum', required=True, type=int)
@click.argument('confirm_sig_hex', required=True)
@click.argument('account', required=True)
@click.pass_obj
def challenge_exit(client, blknum, confirm_sig_hex, account):
    confirmSig = utils.decode_hex(confirm_sig_hex)
    client.challenge_exit(blknum, confirmSig, account)
    print("Submitted challenge exit")

@cli.command()
@click.argument('sender', required=True)
@click.argument('key', required=True)
@click.pass_obj
def register(client, sender, key):
    _key = utils.decode_hex(key)
    client.register(sender, _key)
    print("Registered")

if __name__ == '__main__':
    cli()
