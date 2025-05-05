from nectar import Hive
from nectar.nodelist import NodeList

from hive_sbi.hsbi.transfer_ops_storage import AccountTrx
from hive_sbi.hsbi.utils import (
    load_config,
    measure_execution_time,
    setup_database_connections,
    setup_storage_objects,
)


def run():
    """Run the compare operations database module"""
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
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Setup Hive connection
    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"Could not update nodes: {str(e)}")
    # Initialize Hive connection for potential future use
    # Not directly used in this file but kept for consistency with other modules
    _ = Hive(node=nodes.get_nodes(hive=hive_blockchain))

    print("Checking account history operations...")

    # Initialize account transaction storage
    accountTrx = {}
    for account in accounts:
        accountTrx[account] = AccountTrx(db, account)
        if not accountTrx[account].exists_table():
            accountTrx[account].create_table()
    accountTrx["sbi"] = AccountTrx(db, "sbi")

    ops1 = accountTrx["steembasicincome"].get_all(op_types=["transfer", "delegate_vesting_shares"])
    ops2 = accountTrx["sbi"].get_all(op_types=["transfer", "delegate_vesting_shares"])

    print(f"Operations loaded: steembasicincome: {len(ops1)}, sbi: {len(ops2)}")

    # Find missing operations in sbi
    missing_ops_sbi = []
    for op in ops1:
        found = False
        for op2 in ops2:
            if op["index"] == op2["index"]:
                found = True
                break
        if not found:
            missing_ops_sbi.append(op)

    print(f"Missing operations from sbi: {len(missing_ops_sbi)}")

    # Find missing operations in steembasicincome
    missing_ops_steembasicincome = []
    for op in ops2:
        found = False
        for op2 in ops1:
            if op["index"] == op2["index"]:
                found = True
                break
        if not found:
            missing_ops_steembasicincome.append(op)

    print(f"Missing operations from steembasicincome: {len(missing_ops_steembasicincome)}")

    print(f"Operation comparison completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
