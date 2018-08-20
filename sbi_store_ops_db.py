from beem.account import Account
from beem.amount import Amount
from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList
from beem.blockchain import Blockchain
from beem.utils import formatTimeString, addTzInfo
from datetime import datetime
import re
import os
import json
from steembi.transfer_ops_storage import TransferTrx, AccountTrx
import dataset


if __name__ == "__main__":
    config_file = 'config.json'
    if not os.path.isfile(config_file):
        accounts = ["steembasicincome", "sbi2", "sbi3", "sbi4", "sbi5", "sbi6", "sbi7", "sbi8", "sbi9"]
        path = "E:\\sbi\\"
        database = "sbi_ops.sqlite"
        database_transfer = "sbi_transfer.sqlite"
        databaseConnector = None
        other_accounts = ["minnowbooster"]
    else:
        with open(config_file) as json_data_file:
            config_data = json.load(json_data_file)
        # print(config_data)
        accounts = config_data["accounts"]
        path = config_data["path"]
        database = config_data["database"]
        database_transfer = config_data["database_transfer"]
        databaseConnector = config_data["databaseConnector"]
        other_accounts = config_data["other_accounts"]
    
    # sqlDataBaseFile = os.path.join(path, database)
    # databaseConnector = "sqlite:///" + sqlDataBaseFile
    db = dataset.connect(databaseConnector)    
    
    # Update current node list from @fullnodeupdate
    nodes = NodeList()
    # nodes.update_nodes(weights={"hist": 1})
    stm = Steem(node=nodes.get_nodes(appbase=False, https=False))
    print(str(stm))
    set_shared_steem_instance(stm)
    
    blockchain = Blockchain()
    
    
    accountTrx = {}
    for account in accounts:
        accountTrx[account] = AccountTrx(db, account)
        if not accountTrx[account].exists_table():
            accountTrx[account].create_table()

    # stop_index = addTzInfo(datetime(2018, 7, 21, 23, 46, 00))
    # stop_index = formatTimeString("2018-07-21T23:46:09")
    
    for account_name in accounts:
        account = Account(account_name)
        
        # Go trough all transfer ops
        cnt = 0

        start_index = accountTrx[account_name].get_latest_index()
        if start_index is not None:
            start_index = start_index["op_acc_index"] + 1
            print("account %s - %d" % (account["name"], start_index))
        data = []
        for op in account.history(start=start_index, use_block_num=False):
            virtual_op = op["virtual_op"]
            trx_in_block = op["trx_in_block"]
            if virtual_op > 0:
                trx_in_block = -1
            d = {"block": op["block"], "op_acc_index": op["index"], "op_acc_name": account["name"], "trx_in_block": trx_in_block,
                 "op_in_trx": op["op_in_trx"], "virtual_op": virtual_op,  "timestamp": formatTimeString(op["timestamp"]), "type": op["type"], "op_dict": json.dumps(op)}
            data.append(d)
            if cnt % 1000 == 0:
                print(op["timestamp"])
                accountTrx[account_name].add_batch(data)
                data = []
            cnt += 1
        if len(data) > 0:
            print(op["timestamp"])
            accountTrx[account_name].add_batch(data)
            data = []            

    
    # Create keyStorage
    trxStorage = TransferTrx(db)
    
    if not trxStorage.exists_table():
        trxStorage.create_table()
    for account in other_accounts:
        account = Account(account)
        cnt = 0

        start_index = trxStorage.get_latest_index(account["name"])
        if start_index is not None:
            start_index = start_index["op_acc_index"] + 1            
            print("account %s - %d" % (account["name"], start_index))
        data = []
        for op in account.history(start=start_index, use_block_num=False, only_ops=["transfer"]):
            amount = Amount(op["amount"])
            virtual_op = op["virtual_op"]
            trx_in_block = op["trx_in_block"]
            if virtual_op > 0:
                trx_in_block = -1
            memo = ascii(op["memo"])
            d = {"block": op["block"], "op_acc_index": op["index"], "op_acc_name": account["name"], "trx_in_block": trx_in_block,
                 "op_in_trx": op["op_in_trx"], "virtual_op": virtual_op, "timestamp": formatTimeString(op["timestamp"]), "from": op["from"], "to": op["to"],
                    "amount": amount.amount, "amount_symbol": amount.symbol, "memo": memo, "op_type": op["type"]}
            data.append(d)
            if cnt % 1000 == 0:
                print(op["timestamp"])
                trxStorage.add_batch(data)
                data = []
            cnt += 1
        if len(data) > 0:
            print(op["timestamp"])
            trxStorage.add_batch(data)
            data = []
