import time

from nectar import Hive
from nectar.nodelist import NodeList

from hive_sbi.hsbi.core import (
    get_logger,
    load_config,
    setup_database_connections,
    setup_storage_objects,
)
from hive_sbi.hsbi.utils import measure_execution_time

logger = get_logger()


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
        logger.warning(f"could not update nodes: {str(e)}")
    hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))

    # Check member database
    logger.info("Checking member database...")
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
            logger.warning(f"Missing management account: {d['sponsor']}")
            missing_accounts.append(d["sponsor"])
            aborted = True
        elif d["share_type"] == "Delegation" and d["sponsor"] not in member_accounts:
            logger.warning(f"Missing delegation account: {d['sponsor']}")
            missing_accounts.append(d["sponsor"])
            aborted = True
        elif d["share_type"] == "Delegation" and d["sponsor"] in member_accounts:
            continue
        elif d["sponsor"] not in member_accounts:
            logger.warning(f"Missing account: {d['sponsor']}")
            missing_accounts.append(d["sponsor"])
            aborted = True

    if aborted:
        logger.warning("Please fix the missing accounts first!")
        logger.warning(f"Missing accounts: {', '.join(missing_accounts)}")
    else:
        logger.info("Member database check is OK!")

    logger.info(
        f"Member database check completed in {measure_execution_time(start_time):.2f} seconds"
    )

    shares = 0
    bonus_shares = 0
    balance_rshares = 0
    for m in member_data:
        shares += member_data[m]["shares"]
        bonus_shares += member_data[m]["bonus_shares"]
        balance_rshares += member_data[m]["balance_rshares"]

    logger.info("units: %d" % shares)
    logger.info("bonus units: %d" % bonus_shares)
    logger.info("total units: %d" % (shares + bonus_shares))
    logger.info("----------")
    logger.info("balance_rshares: %d" % balance_rshares)
    logger.info("balance_rshares: %.3f $" % hv.rshares_to_hbd(balance_rshares))
    if len(missing_accounts) > 0:
        logger.warning("%d not existing accounts: " % len(missing_accounts))
        logger.warning(missing_accounts)
