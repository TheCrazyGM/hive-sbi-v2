import json
import time
from datetime import datetime, timezone

from nectar import Hive
from nectar.account import Account
from nectar.amount import Amount
from nectar.nodelist import NodeList
from nectar.utils import formatTimeString

from hive_sbi.hsbi.transfer_ops_storage import AccountTrx


def get_account_trx_data(account, start_block, start_index):
    # Go through all transfer ops
    if start_block is not None:
        # Check if start_block is a dictionary or an integer
        if isinstance(start_block, dict):
            trx_in_block = start_block["trx_in_block"]
            op_in_trx = start_block["op_in_trx"]
            virtual_op = start_block["virtual_op"]
            block_num = start_block["block"]
            print("account %s - %d" % (account["name"], block_num))
        else:
            # start_block is already a block number
            block_num = start_block
            trx_in_block = 0
            op_in_trx = 0
            virtual_op = False
            print("account %s - %d" % (account["name"], block_num))
    else:
        block_num = 0
        trx_in_block = 0
        op_in_trx = 0
        virtual_op = False

    # Check if start_index is a dictionary or an integer
    if start_index is not None:
        if isinstance(start_index, dict) and "op_acc_index" in start_index:
            start_index = start_index["op_acc_index"] + 1
        # If it's already an integer, use it as is
    else:
        start_index = 0

    data = []
    last_block = 0
    last_trx = trx_in_block
    for op in account.history(start=start_block - 5, use_block_num=True):
        if op["block"] < start_block:
            # last_block = op["block"]
            continue
        elif op["block"] == start_block:
            if op["virtual_op"] == 0:
                if op["trx_in_block"] < trx_in_block:
                    last_trx = op["trx_in_block"]
                    continue
                if op["op_in_trx"] <= op_in_trx and (trx_in_block != last_trx or last_block == 0):
                    continue
            else:
                if op["virtual_op"] <= virtual_op and (trx_in_block == last_trx):
                    continue
        start_block = op["block"]
        virtual_op = op["virtual_op"]
        trx_in_block = op["trx_in_block"]

        if trx_in_block != last_trx or op["block"] != last_block:
            op_in_trx = op["op_in_trx"]
        else:
            op_in_trx += 1
        if virtual_op > 0:
            op_in_trx = 0
            if trx_in_block > 255:
                trx_in_block = 0

        d = {
            "block": op["block"],
            "op_acc_index": start_index,
            "op_acc_name": account["name"],
            "trx_in_block": trx_in_block,
            "op_in_trx": op_in_trx,
            "virtual_op": virtual_op,
            "timestamp": formatTimeString(op["timestamp"]),
            "type": op["type"],
            "op_dict": json.dumps(op),
        }
        # op_in_trx += 1
        start_index += 1
        last_block = op["block"]
        last_trx = trx_in_block
        data.append(d)
    return data


def get_account_trx_storage_data(account, start_index, hv):
    if start_index is not None:
        start_index = start_index["op_acc_index"] + 1
        print("account %s - %d" % (account["name"], start_index))

    data = []
    for op in account.history(start=start_index, use_block_num=False, only_ops=["transfer"]):
        amount = Amount(op["amount"], blockchain_instance=hv)
        virtual_op = op["virtual_op"]
        trx_in_block = op["trx_in_block"]
        if virtual_op > 0:
            trx_in_block = -1
        memo = ascii(op["memo"])
        d = {
            "block": op["block"],
            "op_acc_index": op["index"],
            "op_acc_name": account["name"],
            "trx_in_block": trx_in_block,
            "op_in_trx": op["op_in_trx"],
            "virtual_op": virtual_op,
            "timestamp": formatTimeString(op["timestamp"]),
            "from": op["from"],
            "to": op["to"],
            "amount": amount.amount,
            "amount_symbol": amount.symbol,
            "memo": memo,
            "op_type": op["type"],
        }
        data.append(d)
    return data


def run():
    from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
    from hive_sbi.hsbi.utils import measure_execution_time

    # Initialize start time for measuring execution time
    start_prep_time = time.time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get accounts directly from storage
    accounts = storage["accounts"]
    other_accounts = storage["other_accounts"]

    # Get hive_blockchain setting
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Get configuration directly from storage
    conf_setup = storage["conf_setup"]
    last_cycle = conf_setup["last_cycle"]
    share_cycle_min = conf_setup["share_cycle_min"]

    # Ensure last_cycle has timezone information
    if last_cycle is not None and last_cycle.tzinfo is None:
        last_cycle = last_cycle.replace(tzinfo=timezone.utc)

    print(
        "sbi_store_ops_db: last_cycle: %s - %.2f min"
        % (
            formatTimeString(last_cycle),
            (datetime.now(timezone.utc) - last_cycle).total_seconds() / 60,
        )
    )

    if (
        last_cycle is not None
        and (datetime.now(timezone.utc) - last_cycle).total_seconds() > 60 * share_cycle_min
    ):
        # Update current node list from @fullnodeupdate
        nodes = NodeList()
        nodes.update_nodes()
        # nodes.update_nodes(weights={"hist": 1})
        hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))
        print(str(hv))

        print("Fetch new account history ops.")

        # Blockchain instance is not needed here

        accountTrx = {}
        for account in accounts:
            if account == "steembasicincome":
                accountTrx["sbi"] = AccountTrx(db, "sbi")
            else:
                accountTrx[account] = AccountTrx(db, account)

        # stop_index = addTzInfo(datetime(2018, 7, 21, 23, 46, 00))
        # stop_index = formatTimeString("2018-07-21T23:46:09")

        for account_name in accounts:
            if account_name == "steembasicincome":
                account = Account(account_name, blockchain_instance=hv)
                account_name = "sbi"
            else:
                account = Account(account_name, blockchain_instance=hv)
            start_block = accountTrx[account_name].get_latest_block_num()
            start_index = accountTrx[account_name].get_latest_trx_index(start_block) if start_block is not None else 0

            data = get_account_trx_data(account, start_block, start_index)

            data_batch = []
            for cnt in range(0, len(data)):
                data_batch.append(data[cnt])
                if cnt % 1000 == 0:
                    # Add each transaction individually since add_batch is not available
                    for trx in data_batch:
                        accountTrx[account_name].add(trx)
                    data_batch = []
            if len(data_batch) > 0:
                # Add each transaction individually since add_batch is not available
                for trx in data_batch:
                    accountTrx[account_name].add(trx)
                data_batch = []

        # Process other accounts using the trxStorage from the storage objects
        transferTrxStorage = storage["transfer_trx"]

        for account in other_accounts:
            account = Account(account, blockchain_instance=hv)
            start_index = transferTrxStorage.get_latest_index(account["name"])

            data = get_account_trx_storage_data(account, start_index, hv)

            data_batch = []
            for cnt in range(0, len(data)):
                data_batch.append(data[cnt])
                if cnt % 1000 == 0:
                    # Add each transaction individually since add_batch is not available
                    for trx in data_batch:
                        transferTrxStorage.add(trx)
                    data_batch = []
            if len(data_batch) > 0:
                # Add each transaction individually since add_batch is not available
                for trx in data_batch:
                    transferTrxStorage.add(trx)
                data_batch = []
        print(f"store_ops_db script run {measure_execution_time(start_prep_time):.2f} s")


if __name__ == "__main__":
    run()
