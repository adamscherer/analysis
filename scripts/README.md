# Utility Scripts

This directory contains utility scripts for the stocks project.

## Urgent Slack Notifier (MCP Client)

The `urgent_slack_notifier.py` script evaluates text for urgency and sends notifications to Slack using the Model Context Protocol (MCP) Slack server.

### MCP Slack Server Setup

1. Set up the Slack MCP server using one of the following methods:

   #### Using npx (recommended)

   Add the following to your `claude_desktop_config.json` file:
   ```json
   {
     "mcpServers": {
       "slack": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-slack"
         ],
         "env": {
           "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
           "SLACK_TEAM_ID": "T08N6MXCWGG"
         }
       }
     }
   }
   ```

   #### Using Docker

   Add the following to your `claude_desktop_config.json` file:
   ```json
   {
     "mcpServers": {
       "slack": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "-e",
           "SLACK_BOT_TOKEN",
           "-e",
           "SLACK_TEAM_ID",
           "mcp/slack"
         ],
         "env": {
           "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
           "SLACK_TEAM_ID": "T08N6MXCWGG"
         }
       }
     }
   }
   ```

   To build the Docker image:
   ```bash
   docker build -t mcp/slack -f src/slack/Dockerfile .
   ```

2. Install the required dependencies:
   ```bash
   # Using Poetry (recommended)
   poetry add modelcontextprotocol anthropic

   # Using pip
   pip install modelcontextprotocol anthropic
   ```

3. Make sure the following environment variables are set in your `.env` file:
   ```
   SLACK_API_TOKEN=xoxb-your-token-here
   SLACK_NOTIFICATION_CHANNEL=#alerts
   SLACK_TEAM_ID=T08N6MXCWGG
   ```

4. **Important:** Create a Slack App with the following scopes:
   - `channels:history` - View messages and other content in public channels
   - `channels:read` - View basic channel information
   - `chat:write` - Send messages as the app
   - `reactions:write` - Add emoji reactions to messages
   - `users:read` - View users and their basic information

5. Install the Slack App to your workspace and get the Bot User OAuth Token (starts with `xoxb-`).

6. **Important:** Make sure to invite your Slack bot to the channel you want to post to:
   - In Slack, go to the channel
   - Type `/invite @YourBotName` and press Enter

### Usage

```bash
# Basic usage with text from command line
python scripts/urgent_slack_notifier.py "Critical error in production database"

# Read text from a file
python scripts/urgent_slack_notifier.py --file error_log.txt

# Pipe text from another command
tail -n 50 app.log | python scripts/urgent_slack_notifier.py

# Adjust urgency threshold (0.0-1.0, default is 0.7)
python scripts/urgent_slack_notifier.py --threshold 0.5 "Warning: High CPU usage detected"

# Always send notification regardless of urgency
python scripts/urgent_slack_notifier.py --always-notify "FYI: Daily backup completed"

# Evaluate urgency but don't actually send to Slack (dry run)
python scripts/urgent_slack_notifier.py --dry-run "Server restarting in 5 minutes"

# Specify a different channel to send to (overrides .env setting)
python scripts/urgent_slack_notifier.py --channel "#general" "Message to specific channel"

# Use simulation mode (don't actually call MCP)
python scripts/urgent_slack_notifier.py --use-simulation "Testing in simulation mode"
```

### Wrapper Script

A convenience wrapper script `mcp_slack_notify.sh` is provided that will:
1. Start the MCP Slack server (using npx or Docker)
2. Run the urgent_slack_notifier.py script with your arguments
3. Automatically stop the server when done

```bash
# Using npx (default)
./scripts/mcp_slack_notify.sh "Critical error detected"

# Using Docker
./scripts/mcp_slack_notify.sh --docker "Critical error detected"

# All options from urgent_slack_notifier.py can be used
./scripts/mcp_slack_notify.sh --threshold 0.5 --channel "#general" "High CPU usage"
```

This is the recommended way to use the notifier as it handles the MCP server lifecycle automatically.

### Available MCP Slack Tools

The Slack MCP server provides the following tools:

1. `slack_list_channels`: List public channels in the workspace
2. `slack_post_message`: Post a new message to a Slack channel
3. `slack_reply_to_thread`: Reply to a specific message thread
4. `slack_add_reaction`: Add an emoji reaction to a message
5. `slack_get_channel_history`: Get recent messages from a channel
6. `slack_get_thread_replies`: Get all replies in a message thread
7. `slack_get_users`: Get list of workspace users with basic profile information
8. `slack_get_user_profile`: Get detailed profile information for a specific user

Our script currently uses `slack_list_channels` and `slack_post_message`.

### Troubleshooting

#### "not_in_channel" Error

If you see an error message like:
```
Failed to send notification: not_in_channel
```

This means your Slack bot needs to be invited to the channel. In Slack, go to the target channel and type:
```
/invite @YourBotName
```

#### Finding Your Team ID

To find your Slack Team ID:
1. In a web browser, go to your Slack workspace
2. Right-click anywhere and select "Inspect" or "Inspect Element"
3. Go to the "Application" or "Storage" tab
4. Look in Local Storage for entries containing "team_id"
5. The Team ID starts with a "T" followed by alphanumeric characters

### Customization

To modify urgency detection, edit the `URGENT_KEYWORDS` list in the `UrgencyEvaluator` class.

For more advanced urgency detection, consider implementing ML-based text classification. 