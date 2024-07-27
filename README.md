# Enhanced Voting System

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Commands](#commands)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)
10. [License](#license)

## Overview

The Enhanced Voting System is a command-line application designed to manage and facilitate voting processes. It provides features such as voter registration, vote recording, live voting updates, and automated reminders. The system uses Firebase for data storage and includes email and SMS notification capabilities.

## Features

- Voter registration and management
- Secure vote recording
- Live voting updates
- Automated email and SMS reminders
- Voter status queries
- Colorized console output for better readability

## Prerequisites

Before installing the Enhanced Voting System, ensure you have the following:

- Python 3.7 or higher
- pip (Python package installer)
- A Firebase project with Firestore database
- Gmail account for sending emails
- Twilio account for sending SMS (optional)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/enhanced-voting-system.git
   cd enhanced-voting-system
   ```

2. Install required dependencies:
   ```
   pip install firebase-admin pandas openpyxl schedule twilio colorama
   ```

## Configuration

1. Firebase Setup:
   - Create a Firebase project and download the service account key JSON file.
   - Rename the file to `serviceAccountKey.json` and place it in the project root directory.

2. Email Configuration:
   - Open `voting_system.py` and update the following variables:
     ```python
     SMTP_USERNAME = "your-email@gmail.com"
     SMTP_PASSWORD = "your-app-password"  # Use an app password, not your regular password
     ```

3. Twilio Configuration (for SMS):
   - Sign up for a Twilio account and get your account SID, auth token, and a Twilio phone number.
   - Update the following variables in `voting_system.py`:
     ```python
     TWILIO_ACCOUNT_SID = "your-account-sid"
     TWILIO_AUTH_TOKEN = "your-auth-token"
     TWILIO_PHONE_NUMBER = "your-twilio-phone-number"
     ```

## Usage

To start the Enhanced Voting System, run:

```
python voting_system.py
```

You will be greeted with a welcome message and a prompt. Use the available commands to interact with the system.

## Commands

### `import_voters <file_path>`
Import voters from an Excel file.
- `<file_path>`: Path to the Excel file containing voter information.
- Example: `import_voters voters_list.xlsx`

### `record_vote <email> <choice>`
Record a vote for a specific voter.
- `<email>`: Email address of the voter.
- `<choice>`: The voter's choice (e.g., "Yes" or "No").
- Example: `record_vote john@example.com Yes`

### `get_voter_status <email>`
Retrieve the status of a specific voter.
- `<email>`: Email address of the voter.
- Example: `get_voter_status jane@example.com`

### `live_voting`
Start live voting updates. Press Enter to stop.

### `stop_live_voting`
Stop the live voting updates.

### `set_voting_date YYYY-MM-DD`
Set the voting date and schedule reminders.
- Example: `set_voting_date 2024-11-05`

### `list_voters`
Display a list of all registered voters and their voting status.

### `exit`
Exit the Enhanced Voting System.

## Troubleshooting

- If you encounter gRPC warnings, they can be safely ignored as they don't affect the system's functionality.
- Ensure your `serviceAccountKey.json` file is correctly placed and has the necessary permissions.
- For email sending issues, make sure you're using an app password for your Gmail account.
- If SMS sending fails, verify your Twilio account settings and ensure you have sufficient credit.

## Contributing

Contributions to the Enhanced Voting System are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive commit messages.
4. Push your changes to your fork.
5. Submit a pull request to the main repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
