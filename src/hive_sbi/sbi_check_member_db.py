import time

from nectar import Hive
from nectar.nodelist import NodeList

from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
from hive_sbi.hsbi.utils import measure_execution_time


def run():
    """Run the check member database module"""
    start_time = time.time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    trxStorage = storage["trxStorage"]
    memberStorage = storage["memberStorage"]
    confStorage = storage["confStorage"]
    accStorage = storage["accountStorage"]

    # Get configuration values
    accounts = accStorage.get()
    other_accounts = accStorage.get_transfer()
    sp_share_ratio = confStorage.get()["sp_share_ratio"]
    mgnt_shares = config_data.get("mgnt_shares", {})
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Setup Hive connection
    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"could not update nodes: {str(e)}")
    hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))

    # Check member database
    print("Checking member database...")
    member_accounts = memberStorage.get_all_accounts()
    data = trxStorage.get_all_data()

    missing_accounts = []
    member_data = {}
    aborted = False
    for m in member_accounts:
        member_data[m] = memberStorage.get(m)
    for d in data:
        if d["share_type"] == "Mgmt" and d["sponsor"] in member_accounts:
            continue
        elif d["share_type"] == "Mgmt" and d["sponsor"] not in member_accounts:
            print(f"Missing management account: {d['sponsor']}")
            missing_accounts.append(d["sponsor"])
            aborted = True
        elif d["share_type"] == "Delegation" and d["sponsor"] not in member_accounts:
            print(f"Missing delegation account: {d['sponsor']}")
            missing_accounts.append(d["sponsor"])
            aborted = True
        elif d["share_type"] == "Delegation" and d["sponsor"] in member_accounts:
            continue
        elif d["sponsor"] not in member_accounts:
            print(f"Missing account: {d['sponsor']}")
            missing_accounts.append(d["sponsor"])
            aborted = True

    if aborted:
        print("Please fix the missing accounts first!")
        print(f"Missing accounts: {', '.join(missing_accounts)}")
    else:
        print("Member database check is OK!")

    print(f"Member database check completed in {measure_execution_time(start_time):.2f} seconds")

    shares = 0
    bonus_shares = 0
    balance_rshares = 0
    for m in member_data:
        shares += member_data[m]["shares"]
        bonus_shares += member_data[m]["bonus_shares"]
        balance_rshares += member_data[m]["balance_rshares"]

    print("units: %d" % shares)
    print("bonus units: %d" % bonus_shares)
    print("total units: %d" % (shares + bonus_shares))
    print("----------")
    print("balance_rshares: %d" % balance_rshares)
    print("balance_rshares: %.3f $" % hv.rshares_to_hbd(balance_rshares))
    if len(missing_accounts) > 0:
        print("%d not existing accounts: " % len(missing_accounts))
        print(missing_accounts)
