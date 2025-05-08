from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
from hive_sbi.hsbi.transfer_ops_storage import AccountTrx
from hive_sbi.hsbi.utils import measure_execution_time


def run():
    """Run the check transaction database module"""
    start_time = measure_execution_time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    trxStorage = storage["trx"]
    memberStorage = storage["member"]

    # Get all transaction data
    data = trxStorage.get_all_data()

    # Analyze transaction data
    status = {}
    share_type = {}
    n_records = 0
    shares = 0

    for op in data:
        if op["status"] in status:
            status[op["status"]] += 1
        else:
            status[op["status"]] = 1

        if op["share_type"] in share_type:
            share_type[op["share_type"]] += 1
        else:
            share_type[op["share_type"]] = 1

        shares += op["shares"]
        n_records += 1

    # Print results
    print(f"The transaction database has {n_records} records")
    print("Number of shares:")
    print(f"Shares: {shares}")
    print("Status:")
    for s in status:
        print(f"{s}: {status[s]}")

    print("Share type:")
    for s in share_type:
        print(f"{s}: {share_type[s]}")

    # Check account transactions
    accountTrx = {}
    accounts = config_data.get("accounts", [])

    for account in accounts:
        if account == "steembasicincome":
            accountTrx["sbi"] = AccountTrx(db, "sbi")
        else:
            accountTrx[account] = AccountTrx(db, account)

    for account_name in accountTrx:
        data = accountTrx[account_name].get_all()
        print(f"Account {account_name} has {len(data)} entries")

    print(
        f"Transaction database check completed in {measure_execution_time(start_time):.2f} seconds"
    )


if __name__ == "__main__":
    run()
