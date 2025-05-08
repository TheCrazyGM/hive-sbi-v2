from datetime import timezone

from nectar import Hive
from nectar.instance import set_shared_blockchain_instance
from nectar.nodelist import NodeList

from hive_sbi.hsbi.core import get_logger
from hive_sbi.hsbi.transfer_ops_storage import TransferTrx

logger = get_logger()


def calculate_shares(delegation_shares, sp_share_ratio):
    return int(delegation_shares / sp_share_ratio)


def run():
    import time

    from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
    from hive_sbi.hsbi.utils import measure_execution_time

    start_time = time.time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get account storage
    accounts = storage["accounts"]
    other_accounts = storage["other_accounts"]

    # Get configuration storage
    confStorage = storage["confStorage"]  # Get the storage object for later updates
    conf_setup = storage["conf_setup"]  # Get the pre-fetched configuration data

    # Get blockchain setting
    hive_blockchain = config_data.get("hive_blockchain", True)

    last_cycle = conf_setup["last_cycle"]
    # Ensure last_cycle has timezone info
    if last_cycle is not None:
        if isinstance(last_cycle, str):
            from datetime import datetime

            from nectar.utils import addTzInfo

            # Try to parse the datetime string directly instead of using formatTimeString
            try:
                # Try ISO format first (2025-01-01T00:00:00)
                last_cycle = datetime.fromisoformat(last_cycle)
            except ValueError:
                try:
                    # Try with space instead of T (2025-01-01 00:00:00)
                    last_cycle = datetime.strptime(last_cycle, "%Y-%m-%d %H:%M:%S%z")
                except ValueError:
                    try:
                        # Try without timezone (2025-01-01 00:00:00)
                        last_cycle = datetime.strptime(last_cycle, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Fall back to original method as last resort
                        from nectar.utils import formatTimeString

                        last_cycle = formatTimeString(last_cycle)

            # Ensure timezone info is added if needed
            if last_cycle.tzinfo is None:
                last_cycle = addTzInfo(last_cycle)
        elif last_cycle.tzinfo is None:
            from nectar.utils import addTzInfo

            last_cycle = addTzInfo(last_cycle)

    share_cycle_min = conf_setup["share_cycle_min"]
    sp_share_ratio = conf_setup["sp_share_ratio"]
    rshares_per_cycle = conf_setup["rshares_per_cycle"]
    last_delegation_check = conf_setup["last_delegation_check"]

    # Ensure last_delegation_check has timezone info
    if last_delegation_check is not None:
        if isinstance(last_delegation_check, str):
            from datetime import datetime

            from nectar.utils import addTzInfo

            # Try to parse the datetime string directly instead of using formatTimeString
            try:
                # Try ISO format first (2025-01-01T00:00:00)
                last_delegation_check = datetime.fromisoformat(last_delegation_check)
            except ValueError:
                try:
                    # Try with space instead of T (2025-01-01 00:00:00)
                    last_delegation_check = datetime.strptime(
                        last_delegation_check, "%Y-%m-%d %H:%M:%S%z"
                    )
                except ValueError:
                    try:
                        # Try without timezone (2025-01-01 00:00:00)
                        last_delegation_check = datetime.strptime(
                            last_delegation_check, "%Y-%m-%d %H:%M:%S"
                        )
                    except ValueError:
                        # Fall back to original method as last resort
                        from nectar.utils import formatTimeString

                        last_delegation_check = formatTimeString(last_delegation_check)

            # Ensure timezone info is added if needed
            if last_delegation_check.tzinfo is None:
                last_delegation_check = addTzInfo(last_delegation_check)
        elif hasattr(last_delegation_check, "tzinfo") and last_delegation_check.tzinfo is None:
            from nectar.utils import addTzInfo

            last_delegation_check = addTzInfo(last_delegation_check)

    # Import formatTimeString here to ensure it's available for the print statement
    from nectar.utils import formatTimeString as format_time_string

    logger.info(
        "sbi_check_delegation: last_cycle: %s - %.2f min"
        % (
            format_time_string(last_cycle),
            (datetime.now(timezone.utc) - last_cycle).total_seconds() / 60,
        )
    )

    if (
        last_cycle is not None
        and (datetime.now(timezone.utc) - last_cycle).total_seconds() > 60 * share_cycle_min
    ):
        nodes = NodeList()
        try:
            nodes.update_nodes()
        except Exception as e:
            logger.info(f"could not update nodes: {str(e)}")
        hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))
        set_shared_blockchain_instance(hv)

        # Get storage objects
        transferStorage = TransferTrx(db)  # TransferTrx only takes db parameter
        trxStorage = storage["trxStorage"]  # Correct key name from setup_storage_objects
        memberStorage = storage["memberStorage"]  # Correct key name from setup_storage_objects

        # Update current node list from @fullnodeupdate

        delegation = {}
        sum_sp = {}
        sum_sp_shares = {}
        sum_sp_leased = {}
        account = "steembasicincome"
        delegation = {}
        delegation_shares = {}
        sum_sp = 0
        sum_sp_leased = 0
        sum_sp_shares = 0
        delegation_timestamp = {}

        logger.info("load delegation")
        delegation_list = []
        for d in trxStorage.get_share_type(share_type="Delegation"):
            if d["share_type"] == "Delegation":
                delegation_list.append(d)
        for d in trxStorage.get_share_type(share_type="DelegationLeased"):
            if d["share_type"] == "DelegationLeased":
                delegation_list.append(d)
        for d in trxStorage.get_share_type(share_type="RemovedDelegation"):
            if d["share_type"] == "RemovedDelegation":
                delegation_list.append(d)

        sorted_delegation_list = sorted(
            delegation_list,
            key=lambda x: (datetime.now(timezone.utc) - x["timestamp"]).total_seconds(),
            reverse=True,
        )

        for d in sorted_delegation_list:
            if d["share_type"] == "Delegation":
                delegation[d["account"]] = hv.vests_to_hp(float(d["vests"]))
                delegation_timestamp[d["account"]] = d["timestamp"]
                delegation_shares[d["account"]] = d["shares"]
            elif d["share_type"] == "DelegationLeased":
                delegation[d["account"]] = 0
                delegation_timestamp[d["account"]] = d["timestamp"]
                delegation_shares[d["account"]] = d["shares"]
            elif d["share_type"] == "RemovedDelegation":
                delegation[d["account"]] = 0
                delegation_timestamp[d["account"]] = d["timestamp"]
                delegation_shares[d["account"]] = 0

        delegation_leased = {}
        delegation_shares = {}
        logger.info("update delegation")
        delegation_account = delegation
        for acc in delegation_account:
            if delegation_account[acc] == 0:
                continue
            if (
                last_delegation_check is not None
                and delegation_timestamp[acc] <= last_delegation_check
            ):
                continue
            if (
                last_delegation_check is not None
                and last_delegation_check < delegation_timestamp[acc]
            ):
                last_delegation_check = delegation_timestamp[acc]
            elif last_delegation_check is None:
                last_delegation_check = delegation_timestamp[acc]
            # if acc in delegation_shares and delegation_shares[acc] > 0:
            #    continue
            logger.info(acc)
            leased = transferStorage.find(acc, account)
            if len(leased) == 0:
                delegation_shares[acc] = delegation_account[acc]
                shares = calculate_shares(delegation_account[acc], sp_share_ratio)
                trxStorage.update_delegation_shares(account, acc, shares)
                continue
            delegation_leased[acc] = delegation_account[acc]
            trxStorage.update_delegation_state(account, acc, "Delegation", "DelegationLeased")
            logger.info("set delegration from %s to leased" % acc)

        dd = delegation
        for d in dd:
            sum_sp += dd[d]
        dd = delegation_leased
        for d in dd:
            sum_sp_leased += dd[d]
        dd = delegation_shares
        for d in dd:
            sum_sp_shares += dd[d]
    confStorage.update({"last_cycle": datetime.now(timezone.utc)})

    logger.info(f"Last delegation check: {format_time_string(last_delegation_check)}")
    logger.info(f"Delegation check completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
