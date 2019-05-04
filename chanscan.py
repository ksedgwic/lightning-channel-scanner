#!/usr/bin/env python3

import os
import sys
from datetime import datetime
import threading

from rpchost import RPCHost

rpc_port = int(os.getenv('RPC_PORT', '8332'))
rpc_user = os.getenv('RPC_USER', '')
rpc_pass = os.getenv('RPC_PASS', '')

#Accessing the RPC local server
url = 'http://' + rpc_user + ':' + rpc_pass + '@localhost:' + str(rpc_port)

host = RPCHost(url)

def scan_block_height(height):
    # print(height)
    hash = host.call('getblockhash', height)
    return scan_block_hash(hash)

def scan_block_hash(hash):
    block = host.call('getblock', hash)
    for txid in block['tx']:
        scan_tx_id(txid)
    return block

def scan_tx_id(txid):
    tx = host.call('getrawtransaction', txid, True)
    is_unilateral_close(tx)

# This is the delayed redemption
def is_unilateral_close(tx):
    retval = False
    for ndx, inp in enumerate(tx['vin']):
        if 'txinwitness' in inp:
            asms = match_unilateral_txinwitness(tx, inp)
            if asms:
                retval = True
    return retval

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

        lockblocks = int(asms[3])
        block0, tstamp0 = tx_height(inp['txid'])
        block1, tstamp1 = block_height(tx['blockhash'])
        delta = block1 - block0

        tstamp_str = datetime.utcfromtimestamp(tstamp1).strftime('%Y-%m-%d %H:%M:%S')
        
        # Check the witness args to see if this is a REMEDY
        if txinwitness[1]:
            typestr = "REMEDY    "
        else:
            typestr = "UNILATERAL"
            
        print('%d %s %d %s %s %d %d' % (
            tstamp1, tstamp_str, block1, typestr, tx['txid'], lockblocks, delta))
        return asms
    
    return None

def tx_height(txid):
    tx = host.call('getrawtransaction', txid, True)
    return block_height(tx['blockhash'])

def block_height(blockhash):
    blk = host.call('getblock', blockhash)
    return blk['height'], blk['time']

lock = threading.Lock()
blockheight = 532590
blockheight = 532446
blockheight = 548258 # 11/1/2018, 12:01:22 AM PDT
blockheight = 557930 # shortly before REMEDY
blockheight = 502000 # Jan 1 2018

def scan_thread():
    global lock, blockheight
    while True:
        with lock:
            bh = blockheight
            blockheight += 1
        scan_block_height(blockheight)

if __name__ == '__main__':

    threads = []
    for ndx in range(0, 10):
        thrd = threading.Thread(target=scan_thread)
        thrd.start()
        threads.append(thrd)

    for thrd in threads:
        thrd.join()
