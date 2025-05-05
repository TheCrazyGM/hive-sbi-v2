#!/usr/bin/env python3

import getpass

from hive_sbi.hsbi.core import load_config
from hive_sbi.hsbi.init_db import init_database
from hive_sbi.hsbi.storage import KeysDB


def add_key(account, key_type, wif, config_file="config.json"):
    """Add a key to the database"""
    # Initialize database if needed
    init_database(config_file=config_file)

    # Load configuration
    config_data = load_config(config_file)

    # Connect to database
    import dataset

    db2 = dataset.connect(config_data["databaseConnector2"])

    # Add key to database
    key_storage = KeysDB(db2)
    key_storage.add(account, key_type, wif)
    print(f"Added {key_type} key for {account}")


def main():
    print("=== Add Hive Keys to Database ===")
    print("This script will add your Hive keys to the database.")
    print("WARNING: Keys will be stored in plain text in the database.")
    print("Make sure your database is secure and not accessible to unauthorized users.")
    print("")

    # Get account name
    account = input("Enter account name: ")

    # Get key type
    print("\nKey types:")
    print("1. Posting")
    print("2. Active")
    key_type_choice = input("Enter key type (1-2): ")
    if key_type_choice == "1":
        key_type = "posting"
    elif key_type_choice == "2":
        key_type = "active"
    else:
        print("Invalid choice. Exiting.")
        return

    # Get private key
    wif = getpass.getpass("Enter private key (WIF): ")

    # Add key to database
    add_key(account, key_type, wif)


if __name__ == "__main__":
    main()
