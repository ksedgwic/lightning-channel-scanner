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
    for inp in tx['vin']:
        if 'txinwitness' in inp:
            asms = scan_txinwitness(inp['txinwitness'])
            if asms:
                print('%s:\n%s' % (txid, asms))

def scan_txinwitness(txinwitness):
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
        return asms
    
    return None

if __name__ == '__main__':
    blockheight = 532590
    while True:
        scan_block_height(blockheight)
        blockheight += 1
