#!/usr/bin/env python3

import datetime

from dateutil.parser import parse
from nectar.utils import addTzInfo

from hive_sbi.hsbi.core import load_config, setup_database_connections
from hive_sbi.hsbi.storage import (
    AccountsDB,
    ConfigurationDB,
    KeysDB,
    MemberDB,
    TransactionMemoDB,
    TransferMemoDB,
    TrxDB,
)


def reset_database():
    """Reset the database by deleting all tables except the keys table"""
    print("Resetting database...")

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Keep the keys
    keys_db = KeysDB(db2)
    keys = []
    if keys_db.exists_table():
        table = db2[keys_db.__tablename__]
        for key in table.all():
            keys.append(key)

    # Delete all tables except keys
    # First, let's wipe the tables in db
    for table_name in db.tables:
        if table_name != keys_db.__tablename__:
            table = db[table_name]
            table.drop()

    # Now, let's wipe the tables in db2 (except keys)
    for table_name in db2.tables:
        if table_name != keys_db.__tablename__:
            table = db2[table_name]
            table.drop()

    # Recreate the keys table and restore the keys
    keys_db = KeysDB(db2)
    keys_db.create_table()
    for key in keys:
        keys_db.add(key["account"], key["key_type"], key["wif"], key["pub_key"])

    # Initialize the database with empty tables
    accounts_db = AccountsDB(db2)
    accounts_db.create_table()

    config_db = ConfigurationDB(db2)
    config_db.create_table()

    # Add default configuration from config.json
    example_config = load_config()

    # Add configuration settings
    config_data = {}
    for key, value in example_config.items():
        if key not in [
            "databaseConnector",
            "databaseConnector2",
            "accounts",
            "other_accounts",
            "mgnt_shares",
        ]:
            # Convert string datetime values to datetime objects
            if (
                key in ["last_cycle", "last_paid_post", "last_paid_comment"]
                and value is not None
            ):
                if isinstance(value, str):
                    try:
                        value = addTzInfo(parse(value))
                    except Exception as e:
                        print(
                            f"Error parsing datetime {key}: {value}. Error: {str(e)}. Using current time."
                        )
                        value = addTzInfo(datetime.datetime.now())
            config_data[key] = value
    config_db.set(config_data)

    # Add accounts from config
    for account in config_data.get("accounts", []):
        account_data = {
            "name": account,
            "voting": True,
            "transfer": False,
        }
        accounts_db.add(account_data)

    # Add other accounts from config
    for account in config_data.get("other_accounts", []):
        account_data = {
            "name": account,
            "voting": False,
            "transfer": True,
        }
        accounts_db.add(account_data)

    # Create other tables
    member_db = MemberDB(db2)
    member_db.create_table()

    trx_db = TrxDB(db2)
    trx_db.create_table()

    transaction_memo_db = TransactionMemoDB(db2)
    transaction_memo_db.create_table()

    transfer_memo_db = TransferMemoDB(db2)
    transfer_memo_db.create_table()

    print("Database reset complete.")


if __name__ == "__main__":
    reset_database()
