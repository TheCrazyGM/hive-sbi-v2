from datetime import datetime

import dataset
from dateutil.parser import parse

from hive_sbi.hsbi.core import load_config
from hive_sbi.hsbi.storage import AccountsDB, KeysDB


def init_database(config_file="config.json"):
    """
    Initialize the database with configuration data from config.json

    Args:
        config_file (str): Path to the configuration file
    """
    # Load configuration
    config_data = load_config(config_file)

    # Connect to databases
    # db = dataset.connect(config_data["databaseConnector"])
    db2 = dataset.connect(config_data["databaseConnector2"])

    # Initialize configuration table
    conf_table = db2["configuration"]

    # Check if configuration exists
    existing_config = conf_table.find_one(id=1)

    if existing_config is None:
        print("Initializing configuration table...")
        # Create configuration record
        # Convert ISO format strings to datetime objects
        now = datetime.now()

        # Helper function to convert string dates to datetime objects
        def parse_date(date_str):
            if isinstance(date_str, str):
                return parse(date_str)
            return date_str or now

        conf_data = {
            "id": 1,
            "last_cycle": parse_date(config_data.get("last_cycle", now)),
            "last_paid_post": parse_date(config_data.get("last_paid_post", now)),
            "last_paid_comment": parse_date(config_data.get("last_paid_comment", now)),
            "share_cycle_min": config_data.get("share_cycle_min", 144000),
            "sp_share_ratio": config_data.get("sp_share_ratio", 2),
            "rshares_per_cycle": config_data.get("rshares_per_cycle", 800000000),
            "minimum_vote_threshold": config_data.get("minimum_vote_threshold", 300000000),
            "comment_vote_divider": config_data.get("comment_vote_divider", 2),
            "comment_vote_timeout_h": config_data.get("comment_vote_timeout_h", 24),
            "upvote_multiplier": config_data.get("upvote_multiplier", 1.05),
            "upvote_multiplier_adjusted": config_data.get("upvote_multiplier_adjusted", 1.05),
            "last_delegation_check": now,
        }
        conf_table.insert(conf_data)
        print("Configuration table initialized.")
    else:
        print("Configuration table already exists.")

    # Initialize accounts table
    accountsDB = AccountsDB(db2)
    if not accountsDB.exists_table():
        accountsDB.create_table()
        # Add accounts from config
        for account in config_data.get("accounts", []):
            accounts_table = db2["accounts"]
            accounts_table.insert(
                {
                    "name": account,
                    "voting": True,
                    "transfer": False,
                }
            )
        # Add other accounts from config
        for account in config_data.get("other_accounts", []):
            accounts_table = db2["accounts"]
            accounts_table.insert(
                {
                    "name": account,
                    "voting": False,
                    "transfer": True,
                }
            )
        print("Accounts table initialized.")
    else:
        print("Accounts table already exists.")

    # Initialize keys table
    keysDB = KeysDB(db2)
    if not keysDB.exists_table():
        keysDB.create_table()
        print("Keys table initialized.")
    else:
        print("Keys table already exists.")

    print("Database initialization complete.")


if __name__ == "__main__":
    init_database()
