from hive_sbi.hsbi.utils import get_elapsed_time_minutes


def is_new_cycle(conf_setup, print_info=True):
    """
    Check if it's time for a new cycle

    Args:
        conf_setup (dict): Configuration setup from ConfigurationDB
        print_info (bool): Whether to print cycle information

    Returns:
        bool: True if it's time for a new cycle, False otherwise
    """
    last_cycle = conf_setup.get("last_cycle")
    share_cycle_min = conf_setup.get("share_cycle_min")

    if last_cycle is None:
        return True

    # Check if enough time has passed since the last cycle
    elapsed_minutes = get_elapsed_time_minutes(last_cycle)

    if print_info:
        from nectar.utils import formatTimeString

        print(f"Last cycle: {formatTimeString(last_cycle)} - {elapsed_minutes:.2f} min")

    return elapsed_minutes > share_cycle_min


def get_cycle_config(conf_setup):
    """
    Get cycle configuration parameters

    Args:
        conf_setup (dict): Configuration setup from ConfigurationDB

    Returns:
        dict: Cycle configuration parameters
    """
    return {
        "last_cycle": conf_setup.get("last_cycle"),
        "share_cycle_min": conf_setup.get("share_cycle_min"),
        "sp_share_ratio": conf_setup.get("sp_share_ratio"),
        "rshares_per_cycle": conf_setup.get("rshares_per_cycle"),
        "del_rshares_per_cycle": conf_setup.get("del_rshares_per_cycle"),
        "upvote_multiplier": conf_setup.get("upvote_multiplier"),
        "last_paid_post": conf_setup.get("last_paid_post"),
        "last_paid_comment": conf_setup.get("last_paid_comment"),
    }
