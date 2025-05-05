import json
import time
from datetime import datetime

from nectar import Hive
from nectar.account import Account
from nectar.nodelist import NodeList
from nectar.utils import formatTimeString

from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
from hive_sbi.hsbi.utils import measure_execution_time


def fix_account_names(account_names):
    """
    Fix account names by ensuring they are lowercase and trimmed

    Args:
        account_names (list): List of account names to fix

    Returns:
        list: List of fixed account names
    """
    fixed_accounts = []
    for account in account_names:
        if account is None:
            continue
        # Convert to string if not already
        if not isinstance(account, str):
            account = str(account)
        # Trim whitespace and convert to lowercase
        account = account.strip().lower()
        if account and account not in fixed_accounts:
            fixed_accounts.append(account)
    return fixed_accounts


def validate_accounts(account_names, hive_instance=None):
    """
    Validate account names by checking if they exist on the blockchain

    Args:
        account_names (list): List of account names to validate
        hive_instance (Hive, optional): Hive instance to use

    Returns:
        tuple: (valid_accounts, invalid_accounts)
    """
    if hive_instance is None:
        nodes = NodeList()
        nodes.update_nodes()
        hive_instance = Hive(node=nodes.get_nodes())

    valid_accounts = []
    invalid_accounts = []

    for account in account_names:
        try:
            Account(account, blockchain_instance=hive_instance)
            valid_accounts.append(account)
        except Exception:
            invalid_accounts.append(account)

    return valid_accounts, invalid_accounts


def fix_member_data(member_data):
    """
    Fix member data by ensuring all required fields are present and formatted correctly

    Args:
        member_data (dict): Member data to fix

    Returns:
        dict: Fixed member data
    """
    # Ensure all required fields are present
    required_fields = [
        "name",
        "shares",
        "bonus_shares",
        "earned_rshares",
        "rewarded_rshares",
        "balance_rshares",
        "curation_rshares",
        "delegation_rshares",
        "other_rshares",
        "subscribed_rshares",
        "posting_auth",
        "upvote_delay",
        "blacklisted",
        "hivewatchers",
        "buildawhale",
        "comment_upvote",
    ]

    for field in required_fields:
        if field not in member_data:
            if field in ["shares", "bonus_shares"]:
                member_data[field] = 0
            elif field in [
                "earned_rshares",
                "rewarded_rshares",
                "balance_rshares",
                "curation_rshares",
                "delegation_rshares",
                "other_rshares",
                "subscribed_rshares",
            ]:
                member_data[field] = 0
            elif field in ["posting_auth", "blacklisted", "hivewatchers", "buildawhale"]:
                member_data[field] = False
            elif field == "upvote_delay":
                member_data[field] = 300  # Default 5 minutes
            elif field == "comment_upvote":
                member_data[field] = 0

    # Fix datetime fields
    datetime_fields = [
        "original_enrollment",
        "latest_enrollment",
        "updated_at",
        "first_cycle_at",
        "last_received_vote",
        "last_comment",
        "last_post",
    ]

    for field in datetime_fields:
        if field in member_data and member_data[field] is not None:
            if isinstance(member_data[field], str):
                try:
                    # Try to parse the datetime string
                    member_data[field] = datetime.fromisoformat(
                        member_data[field].replace("Z", "+00:00")
                    )
                except ValueError:
                    # If parsing fails, try using formatTimeString
                    try:
                        member_data[field] = formatTimeString(member_data[field])
                    except Exception:
                        # If all parsing fails, set to None
                        member_data[field] = None

    return member_data


def run():
    """
    Run the account fixing utility
    """
    start_time = time.time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    memberStorage = storage["memberStorage"]
    accountStorage = storage["accountStorage"]

    # Get blockchain setting
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Setup Hive instance
    nodes = NodeList()
    nodes.update_nodes()
    hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))

    # Fix account names
    print("Fixing account names...")
    accounts = accountStorage.get()
    fixed_accounts = fix_account_names(accounts)

    # Validate accounts
    print("Validating accounts...")
    valid_accounts, invalid_accounts = validate_accounts(fixed_accounts, hv)

    if invalid_accounts:
        print(f"Found {len(invalid_accounts)} invalid accounts: {', '.join(invalid_accounts)}")

    # Fix member data
    print("Fixing member data...")
    fixed_count = 0
    all_members = memberStorage.get_all_accounts()

    for member_name in all_members:
        member_data = memberStorage.get(member_name)
        fixed_data = fix_member_data(member_data)

        # Check if data was modified
        if json.dumps(member_data, sort_keys=True, default=str) != json.dumps(
            fixed_data, sort_keys=True, default=str
        ):
            memberStorage.update(fixed_data)
            fixed_count += 1

    print(f"Fixed {fixed_count} member records")
    print(f"Account fixing completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
