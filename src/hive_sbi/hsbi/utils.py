import time
from datetime import datetime, timezone


def get_current_time():
    """
    Get current time with timezone info

    Returns:
        datetime: Current time with timezone info
    """
    return datetime.now(timezone.utc)


def get_elapsed_time_minutes(last_time):
    """
    Get elapsed time in minutes since last_time

    Args:
        last_time (datetime or str): Last time with timezone info or as string

    Returns:
        float: Elapsed time in minutes
    """
    if last_time is None:
        return 0

    # Convert string to datetime if needed
    if isinstance(last_time, str):
        from nectar.utils import addTzInfo, formatTimeString

        last_time = addTzInfo(formatTimeString(last_time))

    # Ensure last_time is timezone-aware
    if last_time.tzinfo is None:
        from nectar.utils import addTzInfo

        last_time = addTzInfo(last_time)

    return (get_current_time() - last_time).total_seconds() / 60


def print_elapsed_time(script_name, last_cycle):
    """
    Print elapsed time since last cycle

    Args:
        script_name (str): Name of the script
        last_cycle (datetime): Last cycle time
    """
    elapsed_minutes = get_elapsed_time_minutes(last_cycle)
    print(f"{script_name}: last_cycle: {last_cycle} - {elapsed_minutes:.2f} min")


def measure_execution_time(start_time):
    """
    Measure execution time

    Args:
        start_time (float): Start time from time.time()

    Returns:
        float: Execution time in seconds
    """
    return time.time() - start_time
