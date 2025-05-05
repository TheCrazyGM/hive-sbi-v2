import json

from nectar import Hive
from nectar.account import Account
from nectar.nodelist import NodeList
from nectar.utils import formatTimeString

from hive_sbi.hsbi.transfer_ops_storage import AccountTrx, TransferTrx
from hive_sbi.hsbi.utils import (
    load_config,
    measure_execution_time,
    setup_database_connections,
    setup_storage_objects,
)


def run():
    """Run the check operations database module"""
    start_time = measure_execution_time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    accountStorage = storage["accounts"]

    # Get configuration values
    accounts = accountStorage.get()
    other_accounts = accountStorage.get_transfer()
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Setup Hive connection
    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"Could not update nodes: {str(e)}")
    hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))

    print("Fetching new account history operations...")

    # Initialize account transaction storage
    accountTrx = {}
    for account in accounts:
        accountTrx[account] = AccountTrx(db, account)
        if not accountTrx[account].exists_table():
            accountTrx[account].create_table()

    # Process account history operations for steembasicincome
    for account_name in accounts:
        if account_name != "steembasicincome":
            continue

        account = Account(account_name, blockchain_instance=hv)

        # Go through all transfer ops
        cnt = 0

        start_index = accountTrx[account_name].get_latest_index()
        if start_index is not None:
            start_index = start_index["op_acc_index"] + 1
            print(f"Account {account['name']} - {start_index}")
        else:
            start_index = 0

        data = []
        if account.virtual_op_count() > start_index:
            for op in account.history(start=start_index, use_block_num=False):
                virtual_op = op["virtual_op"]
                trx_in_block = op["trx_in_block"]
                if virtual_op > 0:
                    trx_in_block = -1
                d = {
                    "block": op["block"],
                    "op_acc_index": op["index"],
                    "op_acc_name": account["name"],
                    "trx_in_block": trx_in_block,
                    "op_in_trx": op["op_in_trx"],
                    "virtual_op": virtual_op,
                    "timestamp": formatTimeString(op["timestamp"]),
                    "type": op["type"],
                    "op_dict": json.dumps(op),
                }
                data.append(d)
                if cnt % 1000 == 0:
                    print(f"Processing timestamp: {op['timestamp']}")
                    accountTrx[account_name].add_batch(data)
                    data = []
                cnt += 1

            if len(data) > 0:
                print(f"Processing timestamp: {op['timestamp']}")
                accountTrx[account_name].add_batch(data)
                data = []

    # Second pass for steembasicincome (appears to be duplicated in original code)
    # This section is kept for compatibility with the original code
    for account_name in accounts:
        if account_name != "steembasicincome":
            continue

        account = Account(account_name, blockchain_instance=hv)

        # Go through all transfer ops
        cnt = 0

        start_index = accountTrx[account_name].get_latest_index()
        if start_index is not None:
            start_index = start_index["op_acc_index"] + 1
            print(f"Account {account['name']} - {start_index}")
        else:
            start_index = 0

        data = []
        if account.virtual_op_count() > start_index:
            for op in account.history(start=start_index, use_block_num=False):
                virtual_op = op["virtual_op"]
                trx_in_block = op["trx_in_block"]
                if virtual_op > 0:
                    trx_in_block = -1
                d = {
                    "block": op["block"],
                    "op_acc_index": op["index"],
                    "op_acc_name": account["name"],
                    "trx_in_block": trx_in_block,
                    "op_in_trx": op["op_in_trx"],
                    "virtual_op": virtual_op,
                    "timestamp": formatTimeString(op["timestamp"]),
                    "type": op["type"],
                    "op_dict": json.dumps(op),
                }
                data.append(d)
                if cnt % 1000 == 0:
                    print(f"Processing timestamp: {op['timestamp']}")
                    accountTrx[account_name].add_batch(data)
                    data = []
                cnt += 1

            if len(data) > 0:
                print(f"Processing timestamp: {op['timestamp']}")
                accountTrx[account_name].add_batch(data)
                data = []

    # Process sbi2-sbi10 accounts (currently disabled)
    # Note: This section is disabled with a double continue statement in the original code
    # Keeping it commented out for reference
    """
    for account_name in accounts:
        if account_name == "steembasicincome":
            continue

        account = Account(account_name, blockchain_instance=hv)

        # Go through all transfer ops
        cnt = 0

        start_block = accountTrx[account_name].get_latest_block()
        if start_block is not None:
            start_block = start_block["block"]
            print(f"Account {account['name']} - {start_block}")
        else:
            start_block = 0

        data = []
        if account.virtual_op_count() > start_index:
            for op in account.history(start=start_block, use_block_num=True):
                virtual_op = op["virtual_op"]
                trx_in_block = op["trx_in_block"]
                if virtual_op > 0:
                    trx_in_block = -1
                d = {
                    "block": op["block"],
                    "op_acc_index": op["index"],
                    "op_acc_name": account["name"],
                    "trx_in_block": trx_in_block,
                    "op_in_trx": op["op_in_trx"],
                    "virtual_op": virtual_op,
                    "timestamp": formatTimeString(op["timestamp"]),
                    "type": op["type"],
                    "op_dict": json.dumps(op),
                }
                data.append(d)
                if cnt % 1000 == 0:
                    print(f"Processing timestamp: {op['timestamp']}")
                    accountTrx[account_name].add_batch(data)
                    data = []
                cnt += 1

            if len(data) > 0:
                print(f"Processing timestamp: {op['timestamp']}")
                accountTrx[account_name].add_batch(data)
                data = []
    """

    # Process other accounts (transfer accounts)
    trxStorage = TransferTrx(db)

    if not trxStorage.exists_table():
        trxStorage.create_table()

    for account_name in other_accounts:
        account = Account(account_name, blockchain_instance=hv)
        cnt = 0

        start_index = trxStorage.get_latest_index(account["name"])
        if start_index is not None:
            start_index = start_index["op_acc_index"] + 1
            print(f"Account {account['name']} - {start_index}")
        else:
            start_index = 0

        data = []
        if account.virtual_op_count() > start_index:
            for op in account.history(start=start_index, use_block_num=False):
                virtual_op = op["virtual_op"]
                trx_in_block = op["trx_in_block"]
                if virtual_op > 0:
                    trx_in_block = -1
                d = {
                    "block": op["block"],
                    "op_acc_index": op["index"],
                    "op_acc_name": account["name"],
                    "trx_in_block": trx_in_block,
                    "op_in_trx": op["op_in_trx"],
                    "virtual_op": virtual_op,
                    "timestamp": formatTimeString(op["timestamp"]),
                    "type": op["type"],
                    "op_dict": json.dumps(op),
                }
                data.append(d)
                if cnt % 1000 == 0:
                    print(f"Processing timestamp: {op['timestamp']}")
                    trxStorage.add_batch(data)
                    data = []
                cnt += 1

            if len(data) > 0:
                print(f"Processing timestamp: {op['timestamp']}")
                trxStorage.add_batch(data)
                data = []

    print(
        f"Operations database check completed in {measure_execution_time(start_time):.2f} seconds"
    )


if __name__ == "__main__":
    run()
