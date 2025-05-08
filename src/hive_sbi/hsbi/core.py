import json
import logging
import os

import dataset


def get_logger(name="hive_sbi.hsbi"):
    """
    Return a logger configured for the hive_sbi.hsbi namespace.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def load_config(config_file="config.json"):
    """
    Load configuration from config.json file

    Args:
        config_file (str): Path to the configuration file

    Returns:
        dict: Configuration data
    """
    logger = get_logger()
    # Try multiple paths for the config file
    paths_to_try = [
        config_file,  # Current directory
        os.path.join(os.getcwd(), config_file),  # Absolute path from current directory
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            config_file,
        ),  # Project root
    ]

    config_path = None
    for path in paths_to_try:
        if os.path.isfile(path):
            config_path = path
            break

    if config_path is None:
        raise Exception(
            f"Could not find {config_file} in any of the expected locations: {paths_to_try}"
        )

    logger.info(f"Loading configuration from {config_path}")
    with open(config_path) as json_data_file:
        config_data = json.load(json_data_file)

    return config_data


def setup_database_connections(config_data):
    """
    Set up database connections based on configuration

    Args:
        config_data (dict): Configuration data from config.json

    Returns:
        tuple: (db, db2) - Primary and secondary database connections
    """
    databaseConnector = config_data.get("databaseConnector")
    databaseConnector2 = config_data.get("databaseConnector2")

    db = dataset.connect(databaseConnector)
    db2 = dataset.connect(databaseConnector2)

    return db, db2


def setup_storage_objects(db, db2):
    """
    Set up common storage objects used across scripts

    Args:
        db (dataset.Database): Primary database connection
        db2 (dataset.Database): Secondary database connection

    Returns:
        dict: Dictionary of storage objects
    """
    from hive_sbi.hsbi.storage import (
        AccountsDB,
        BlacklistDB,
        ConfigurationDB,
        KeysDB,
        MemberDB,
        TransactionMemoDB,
        TransferMemoDB,
        TrxDB,
    )

    storage = {}

    # Common storage objects
    storage["accountStorage"] = AccountsDB(db2)
    storage["confStorage"] = ConfigurationDB(db2)
    storage["keyStorage"] = KeysDB(db2)
    storage["memberStorage"] = MemberDB(db2)
    storage["trxStorage"] = TrxDB(db2)
    storage["transactionStorage"] = TransactionMemoDB(db2)
    storage["transferMemosStorage"] = TransferMemoDB(db2)
    storage["blacklistStorage"] = BlacklistDB(db2)

    # Get accounts
    storage["accounts"] = storage["accountStorage"].get()
    storage["other_accounts"] = storage["accountStorage"].get_transfer()

    # Get configuration
    storage["conf_setup"] = storage["confStorage"].get()

    # Get blacklist data
    storage["blacklist"] = storage["blacklistStorage"].get()

    return storage


def setup_account_trx(db, accounts):
    """
    Set up AccountTrx objects for each account

    Args:
        db (dataset.Database): Database connection
        accounts (list): List of account names

    Returns:
        dict: Dictionary of AccountTrx objects
    """
    from hive_sbi.hsbi.transfer_ops_storage import AccountTrx

    accountTrx = {}
    for account in accounts:
        if account == "steembasicincome":
            accountTrx["sbi"] = AccountTrx(db, "sbi")
        else:
            accountTrx[account] = AccountTrx(db, account)

    return accountTrx
