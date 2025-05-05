import json

from nectar import Hive
from nectar.nodelist import NodeList
from nectar.utils import formatTimeString

from hive_sbi.hsbi.member import Member
from hive_sbi.hsbi.utils import (
    load_config,
    measure_execution_time,
    setup_database_connections,
    setup_storage_objects,
)


def run():
    """Run the build member database module"""
    start_time = measure_execution_time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    trxStorage = storage["trx"]
    memberStorage = storage["members"]

    # Get configuration values
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Create tables if they don't exist
    if not trxStorage.exists_table():
        trxStorage.create_table()

    if not memberStorage.exists_table():
        memberStorage.create_table()

    # Update current node list from @fullnodeupdate
    print("Building member database...")

    # Clear existing member data
    accs = memberStorage.get_all_accounts()
    for a in accs:
        memberStorage.delete(a)

    # Setup Hive connection
    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"Could not update nodes: {str(e)}")
    # Initialize Hive connection for potential future use
    # Not directly used in this file but kept for consistency with other modules
    _ = Hive(node=nodes.get_nodes(hive=hive_blockchain))
    # Get all transaction data
    data = trxStorage.get_all_data()
    member_data = {}
    for op in data:
        if op["status"] == "Valid":
            share_type = op["share_type"]
            if share_type in [
                "RemovedDelegation",
                "Delegation",
                "DelegationLeased",
                "Mgmt",
                "MgmtTransfer",
            ]:
                continue
            sponsor = op["sponsor"]
            sponsee = json.loads(op["sponsee"])
            shares = op["shares"]
            if isinstance(op["timestamp"], str):
                timestamp = formatTimeString(op["timestamp"])
            else:
                timestamp = op["timestamp"]
            if shares == 0:
                continue
            if sponsor not in member_data:
                member = Member(sponsor, shares, timestamp)
                member.append_share_age(timestamp, shares)
                member_data[sponsor] = member
            else:
                member_data[sponsor]["latest_enrollment"] = timestamp
                member_data[sponsor]["shares"] += shares
                member_data[sponsor].append_share_age(timestamp, shares)
            if len(sponsee) == 0:
                continue
            for s in sponsee:
                shares = sponsee[s]
                if s not in member_data:
                    member = Member(s, shares, timestamp)
                    member.append_share_age(timestamp, shares)
                    member_data[s] = member
                else:
                    member_data[s]["latest_enrollment"] = timestamp
                    member_data[s]["shares"] += shares
                    member_data[s].append_share_age(timestamp, shares)

    # Remove members with zero or negative shares
    empty_shares = []
    for m in member_data:
        if member_data[m]["shares"] <= 0:
            empty_shares.append(m)

    for del_acc in empty_shares:
        del member_data[del_acc]

    # Calculate share statistics
    shares = 0
    bonus_shares = 0
    for m in member_data:
        member_data[m].calc_share_age()
        shares += member_data[m]["shares"]
        bonus_shares += member_data[m]["bonus_shares"]

    print(f"Shares: {shares}")
    print(f"Bonus shares: {bonus_shares}")
    print(f"Total shares: {shares + bonus_shares}")

    # Save member data to database
    member_list = []
    for m in member_data:
        member_list.append(member_data[m])
    memberStorage.add_batch(member_list)

    print(f"Member database build completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
