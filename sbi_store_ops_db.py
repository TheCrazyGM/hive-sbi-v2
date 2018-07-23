from beem.account import Account
from beem.amount import Amount
from beem import Steem
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList
from beem.utils import formatTimeString
import re
import os
from steembi.sqlite_dict import db_store, db_load, db_append, db_extend, db_has_database, db_has_key
from steembi.ops_storage import store_all_ops, check_all_ops
from steembi.transfer_ops_storage import TransferTrx, AccountTrx


if __name__ == "__main__":
    accounts = ["steembasicincome", "sbi2", "sbi3", "sbi4", "sbi5", "sbi6", "sbi7", "sbi8"]
    path = "E:\\sbi\\"
    database = "sbi_ops.sqlite"
    database_transfer = "sbi_transfer.sqlite"
    databaseConnector = None
    # Update current node list from @fullnodeupdate
    nodes = NodeList()
    nodes.update_nodes(weights={"hist": 1})
    stm = Steem(node=nodes.get_nodes(appbase=False, https=False))
    print(str(stm))
    set_shared_steem_instance(stm)
    
    accountTrxStorage = AccountTrx(path, database_transfer, databaseConnector)
    
    newAccountTrxStorage = False
    if not accountTrxStorage.exists_table():
        newAccountTrxStorage = True
        accountTrxStorage.create_table()    
    
    for account in accounts:
        account = Account(account)
        print("account %s" % account["name"])
        # Go trough all transfer ops
        cnt = 0
        if newAccountTrxStorage:
            ops = []
            start_index = None
        else:
            start_index = accountTrxStorage.get_latest_index(account["name"])
            print(start_index)
        data = []
        for op in account.history(start=start_index, use_block_num=False):
            d = {"block": op["block"], "op_acc_index": op["index"], "op_acc_name": account["name"], "trx_in_block": op["trx_in_block"],
                 "op_in_trx": op["op_in_trx"],  "timestamp": formatTimeString(op["timestamp"]), "op_dict": json.dumps(op)}
            data.append(d)
            if cnt % 1000 == 0:
                print(op["timestamp"])
                accountTrxStorage.add_batch(data)
                data = []
            cnt += 1
    
    other_accounts = ["minnowbooster"]

    
    # Create keyStorage
    trxStorage = TransferTrx(path, database_transfer, databaseConnector)
    
    newTrxStorage = False
    if not trxStorage.exists_table():
        newTrxStorage = True
        trxStorage.create_table()
    for account in other_accounts:
        account = Account(account)
        cnt = 0
        if newTrxStorage:
            ops = []
            start_index = None
        else:
            start_index = trxStorage.get_latest_index(account["name"])
            print(start_index)
        data = []
        for op in account.history(start=start_index, use_block_num=False, only_ops=["transfer"]):
            amount = Amount(op["amount"])
            d = {"block": op["block"], "op_acc_index": op["index"], "op_acc_name": account["name"], "trx_in_block": op["trx_in_block"],
                 "op_in_trx": op["op_in_trx"],  "timestamp": formatTimeString(op["timestamp"]), "from": op["from"], "to": op["to"],
                    "amount": amount.amount, "amount_symbol": amount.symbol, "memo": op["memo"], "op_type": op["type"]}
            data.append(d)
            if cnt % 1000 == 0:
                print(op["timestamp"])
                trxStorage.add_batch(data)
                data = []
            cnt += 1
