import sys
import time

from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
from hive_sbi.hsbi.cycle import is_new_cycle
from hive_sbi.hsbi.init_db import init_database
from hive_sbi.hsbi.utils import measure_execution_time, print_elapsed_time


def run_module(module_name):
    """
    Run a specific SBI module

    Args:
        module_name (str): Name of the module to run
    """
    start_time = time.time()

    # Load configuration
    config_data = load_config()

    # Initialize database if needed
    init_database(config_file="config.json")

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Print elapsed time since last cycle
    print_elapsed_time(module_name, storage["conf_setup"]["last_cycle"])

    # Check if it's time for a new cycle
    if not is_new_cycle(storage["conf_setup"]):
        print(f"{module_name}: Not time for a new cycle yet. Exiting.")
        return

    # Import and run the specific module
    if module_name == "store_ops_db":
        from hive_sbi.sbi_store_ops_db import run
    elif module_name == "transfer":
        from hive_sbi.sbi_transfer import run
    elif module_name == "check_delegation":
        from hive_sbi.sbi_check_delegation import run
    elif module_name == "update_member_db":
        from hive_sbi.sbi_update_member_db import run
    elif module_name == "store_member_hist":
        from hive_sbi.sbi_store_member_hist import run
    elif module_name == "upvote_post_comment":
        from hive_sbi.sbi_upvote_post_comment import run
    elif module_name == "stream_post_comment":
        from hive_sbi.sbi_stream_post_comment import run
    elif module_name == "build_member_db":
        from hive_sbi.sbi_build_member_db import run
    elif module_name == "check_member_db":
        from hive_sbi.sbi_check_member_db import run
    else:
        print(f"Unknown module: {module_name}")
        return

    # Run the module
    run()

    # Print execution time
    print(f"{module_name} script run {measure_execution_time(start_time):.2f} s")


def run_all():
    """
    Run all SBI modules in sequence
    """
    modules = [
        "store_ops_db",
        "transfer",
        "check_delegation",
        "update_member_db",
        "store_member_hist",
        "upvote_post_comment",
        "stream_post_comment",
        "build_member_db",
        "check_member_db",
    ]

    for module in modules:
        print(f"Running {module}...")
        run_module(module)
        print(f"Finished {module}\n")


def main():
    """Entry point for the command-line script."""
    if len(sys.argv) > 1:
        # Run specific module
        run_module(sys.argv[1])
    else:
        # Run all modules
        run_all()


if __name__ == "__main__":
    main()
