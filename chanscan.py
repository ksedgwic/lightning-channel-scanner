#!/usr/bin/env python3

import os
import sys

from rpchost import RPCHost

rpc_port = int(os.getenv('RPC_PORT', '8332'))
rpc_user = os.getenv('RPC_USER', '')
rpc_pass = os.getenv('RPC_PASS', '')

#Accessing the RPC local server
url = 'http://' + rpc_user + ':' + rpc_pass + '@localhost:' + str(rpc_port)

host = RPCHost(url)

def scan_block_height(height):
    print(height)
    hash = host.call('getblockhash', height)
    return scan_block_hash(hash)

def scan_block_hash(hash):
    block = host.call('getblock', hash)
    for txid in block['tx']:
        scan_tx_id(txid)
    return block

def scan_tx_id(txid):
    tx = host.call('getrawtransaction', txid, True)
    
    if is_unilateral_close(tx):
        return

    return
    
    if len(tx['vin']) != 1:
        return False
    inp = tx['vin'][0]
    if 'txinwitness' in inp:
        asms = match_multisig_txinwitness(inp['txinwitness'])
        if asms:
            if tx['locktime'] == 0 and inp['sequence'] == 0xffffffff:
                # print('    MUTUAL: %s' % (tx['txid'],))
                pass
            elif tx['locktime'] != 0 and inp['sequence'] != 0xffffffff:
                print('COMMITMENT: %s' % (tx['txid']))

# This is the delayed redemption
def is_unilateral_close(tx):
    for ndx, inp in enumerate(tx['vin']):
        if 'txinwitness' in inp:
            asms = match_unilateral_txinwitness(tx, inp)
            if asms:
                return True
    return False

def match_multisig_txinwitness(txinwitness):
    # Use the last witness slot
    script = txinwitness[-1]
    decoded = host.call('decodescript', script)
    asms = decoded['asm'].split()

    # 2
    # 03bb196b1967a6ae56040f5ab67ec1185c90c122882f35f977b338f4ec0c8743bd
    # 03dc71022efb8936a3bc852380ff6bc59d6790d070f3a886cb4223812cc1d990fb
    # 2
    # OP_CHECKMULTISIG",

    if len(asms) == 5 \
       and asms[0] == '2' \
       and asms[3] == '2' \
       and asms[4] == 'OP_CHECKMULTISIG':
        return asms
    
    return None

def match_unilateral_txinwitness(tx, inp):
    txinwitness = inp['txinwitness']
    # Use the last witness slot
    script = txinwitness[-1]
    decoded = host.call('decodescript', script)
    asms = decoded['asm'].split()

    # OP_IF
    #   0311271dfc0b80f9b16940f4c568b02f7cedd090a62cafd6b54a35701c79d49711
    # OP_ELSE
    #   144
    #   OP_CHECKSEQUENCEVERIFY
    #   OP_DROP
    #   023eeb6bd60f72a44bfebc0a341f7f280c6ee2469b0f49d9bfe96974bb63bba82e
    # OP_ENDIF
    # OP_CHECKSIG
    
    if len(asms) == 9 \
       and asms[0] == 'OP_IF' \
       and asms[2] == 'OP_ELSE' \
       and asms[4] == 'OP_CHECKSEQUENCEVERIFY' \
       and asms[5] == 'OP_DROP' \
       and asms[7] == 'OP_ENDIF' \
       and asms[8] == 'OP_CHECKSIG':

        # Is this inside the CSV window?
        delta = int(asms[3])
        block0 = tx_height(inp['txid'])
        block1 = block_height(tx['blockhash'])
        ext = '%d < %d' % (block1 - block0, delta)
        if block1 - block0 < delta:
            print('    REMEDY: %s %s' % (tx['txid'], ext))
            sys.exit(0)
        else:
            print('UNILATERAL: %s %s' % (tx['txid'], ext))
        return asms
    
    return None

def tx_height(txid):
    tx = host.call('getrawtransaction', txid, True)
    return block_height(tx['blockhash'])

def block_height(blockhash):
    blk = host.call('getblock', blockhash)
    return blk['height']

if __name__ == '__main__':
    blockheight = 532590
    blockheight = 532446
    while True:
        scan_block_height(blockheight)
        blockheight += 1
