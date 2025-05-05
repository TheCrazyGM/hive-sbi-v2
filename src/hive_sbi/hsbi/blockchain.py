from nectar import Hive
from nectar.account import Account
from nectar.blockchain import Blockchain
from nectar.nodelist import NodeList


def get_hive_instance(config_data, keys=None, account=None):
    """
    Get a Hive blockchain instance with updated nodes

    Args:
        config_data (dict): Configuration data from config.json
        keys (list, optional): List of private keys to use
        account (str, optional): Account name to get keys for

    Returns:
        nectar.Hive: Hive blockchain instance
    """
    hive_blockchain = config_data.get("hive_blockchain")

    # Update current node list from @fullnodeupdate
    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"Could not update nodes: {str(e)}")

    # If no keys provided, try to get them from the database
    if keys is None and account is not None:
        import dataset

        from hive_sbi.hsbi.storage import KeysDB

        # Connect to database
        db2 = dataset.connect(config_data["databaseConnector2"])

        # Get keys from database
        key_storage = KeysDB(db2)
        posting_key = key_storage.get(account, "posting")
        active_key = key_storage.get(account, "active")

        # Create keys list
        keys = []
        if posting_key and "wif" in posting_key:
            keys.append(posting_key["wif"])
        if active_key and "wif" in active_key:
            keys.append(active_key["wif"])

        if not keys:
            print(f"No keys found for account {account}")

    # Create Hive instance
    return Hive(node=hive_blockchain, keys=keys)


def get_blockchain(hive_instance):
    """
    Get a Blockchain instance

    Args:
        hive_instance (nectar.Hive): Hive blockchain instance

    Returns:
        nectar.blockchain.Blockchain: Blockchain instance
    """
    return Blockchain(hive_instance=hive_instance)


def get_account(account_name, hive_instance):
    """
    Get an Account instance

    Args:
        account_name (str): Account name
        hive_instance (nectar.Hive): Hive blockchain instance

    Returns:
        nectar.account.Account: Account instance
    """
    return Account(account_name, hive_instance=hive_instance)
