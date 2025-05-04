# SteemBasicIncome (SBI) Functionality Report

This document provides a comprehensive breakdown of the SteemBasicIncome (SBI) application, describing its core functionality, components, and workflow. This analysis is based on examining the codebase, focusing on the runner script and the files it executes.

## Overview

SteemBasicIncome is a service on the Hive blockchain (previously Steem) that allows users to:

1. Become members through various means, primarily through transfers/donations
2. Accumulate "shares" that determine their upvote weight
3. Receive upvotes on their content based on their share count
4. Delegate Hive Power to receive bonus shares

The application consists of multiple Python scripts that handle different aspects of the service, from storing operations, processing transfers, managing membership data, and upvoting content.

## Core Components and Data Structures

### Databases

- Uses two database connections: `databaseConnector` and `databaseConnector2`
- Various storage classes for different types of data:
  - `AccountsDB`: Manages voting and transfer accounts
  - `MemberDB`: Stores member information and share counts
  - `TrxDB`: Tracks transactions
  - `ConfigurationDB`: Stores system configuration
  - `TransferMemoDB`: Manages transfer memo templates
  - `PostsTrx`: Tracks posts and comments for upvoting
  - `MemberHistDB`: Stores historical member data

### Member Model

The core data structure is the `Member` class, which tracks:

- Basic account information
- Share count (regular shares)
- Bonus shares (from delegations)
- Share age metrics
- rshares balance and distribution
- Upvote timing and preferences

## Application Workflow

The SBI application executes the following scripts in sequence, each handling a specific part of the workflow:

### 1. `sbi_store_ops_db.py`

- Updates the list of blockchain nodes
- Fetches new account history operations from the blockchain
- Stores operations in the database for processing
- Tracks both main SBI accounts and transfer accounts
- Processes both transfer operations and delegation operations

### 2. `sbi_transfer.py`

- Parses transfer operations stored in the database
- Processes incoming transfers to SBI accounts
- Handles membership enrollment and share allocation
- Parses transfer memos for commands and instructions
- Uses `MemoParser` to understand user intentions from memos
- Cleans up certain transactions from system accounts

### 3. `sbi_check_delegation.py`

- Monitors and tracks delegations to the SBI account
- Calculates bonus shares based on SP delegation amounts
- Updates delegation status (active, leased, removed)
- Tracks changes in delegation status
- Uses the delegation ratio to calculate share equivalents

### 4. `sbi_update_member_db.py`

- Central component that updates all member information
- Calculates and records share counts, bonus shares, and delegation shares
- Manages the cycle system for periodic reward distribution
- Sends notification memos to users about various events:
  - Welcome messages for new members
  - Share updates
  - Delegation notifications
  - Sponsorship notifications
- Handles management shares allocation for system accounts
- Produces statistics on total shares and distribution

### 5. `sbi_store_member_hist.py`

- Processes blockchain operations (votes, comments) related to members
- Tracks member content creation (posts and comments)
- Updates member upvote timing preferences based on curation optimization
- Records member engagement metrics
- Cleans up old historical data
- Optimizes future vote timing for maximum curation rewards

### 6. `sbi_upvote_post_comment.py`

- Scans for unvoted content from members
- Calculates appropriate voting power based on member shares
- Implements vote weight calculation and distribution
- Applies vote timing logic based on member optimization preferences
- Manages upvote quotas
- Updates vote status in the database
- Distributes votes across multiple voting accounts to manage voting power

### 7. `sbi_stream_post_comment.py`

- Continuously monitors the blockchain for new posts and comments from members
- Filters content based on blacklists (tags, apps, content)
- Responds to commands like `!sbi status` with member information
- Manages vote timing
- Tracks content for future upvoting
- Updates member activity metrics

## Key Mechanisms

### Share Allocation

- Members receive shares based on their transfers to SBI
- Can specify other accounts in memos to sponsor them
- Shares determine upvote weight
- Share age is tracked for potential future features

### Voting System

- Vote weight is proportional to member shares and bonus shares
- Vote timing is optimized based on analysis of curation rewards
- Voting power is distributed across multiple accounts
- Members receive stronger votes for posts than comments (controlled by divider)
- Minimum vote threshold ensures meaningful vote values
- Uses adaptive vote timing based on historical curation data

### Delegation System

- Members can delegate Hive Power to receive bonus shares
- Delegation shares are calculated based on SP delegation amount
- System detects delegation changes and adjusts bonus shares accordingly
- Delegation tracking for leased and removed delegations

### Cycle System

- Uses a configured cycle time (in minutes)
- At each cycle, members accumulate new voting "rshares"
- Cycle triggers many system maintenance tasks
- Controls the rhythm of the entire application

### Member Communication

- Uses small token transfers with informative memos to notify members
- Provides status updates via comment replies to `!sbi status` commands
- Sends welcome messages, share updates, sponsorship notifications

## Configuration Parameters

Key configuration parameters include:

- `share_cycle_min`: Time between reward cycles in minutes
- `sp_share_ratio`: Conversion ratio from Steem Power to shares
- `rshares_per_cycle`: Regular rewards per cycle
- `del_rshares_per_cycle`: Delegation rewards per cycle
- `upvote_multiplier`: Vote strength multiplier
- `minimum_vote_threshold`: Minimum rshares for a vote
- `comment_vote_divider`: Divider to reduce comment vote weight
- `comment_vote_timeout_h`: Time after which comments are no longer voted

## Optimization Features

- Automatic vote timing optimization based on curation rewards analysis
- Statistical tracking of curation performance
- Adaptive vote delay setting for each member
- Distribution of voting power across multiple accounts

## Operational Flow

1. Store blockchain operations in database
2. Process transfers and delegations
3. Update member database with new shares and metrics
4. Track member activity and content
5. Upvote member content according to share weight
6. Stream and monitor new member content
7. Repeat on a regular cycle

This system creates a self-sustaining membership service where donations translate to upvote support, with enhanced benefits from delegations.

## Areas for Improvement in a Rewrite

1. **Code Structure**: Implement a more modular, class-based architecture
2. **Error Handling**: Improve exception handling and recovery mechanisms
3. **Database Access**: Use an ORM approach with proper migrations
4. **Configuration**: Implement a more robust configuration system
5. **Logging**: Add comprehensive logging throughout the application
6. **Testing**: Add unit and integration tests
7. **Documentation**: Include docstrings and API documentation
8. **Security**: Improve key management and access controls
9. **Performance**: Optimize database operations and blockchain queries
10. **Monitoring**: Add system health monitoring and alerting

The current application works but would benefit from modern Python practices, better architecture, and improved maintainability in a rewrite.
