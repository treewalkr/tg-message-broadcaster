# Telegram Message Broadcaster

Broadcast messages from an official channel to subscribed group chats.

## Quick Start

1. **Create Your Bot:** 
   * Use BotFather to create a new Telegram bot. After creation, you'll receive a unique `BOT_TOKEN`.

2. **Get API Credentials:** 
   * Go to [my.telegram.org](https://my.telegram.org/) using the same Telegram account.
   * Follow the instructions to obtain your `API_ID` and `API_HASH`. These are necessary to initialize the Telethon Python library.

3. **Gather Your Information:**
   * At this point, you should have:
     ```
     API_ID= 
     API_HASH= 
     BOT_TOKEN= 
     ```
   * Update (this) repository secrets and variables using these information.
   * Then you can deploy by creating a new release.

4. **Find Your Channel ID:**
   * After the deployment, invite your newly created bot to the Telegram channel where you want to broadcast messages.
   * In the channel, use the command `/channelid` or `/start`. Either command will reveal the `OFFICIAL_CHANNEL_ID` in the bot's response.

5. Update `OFFICIAL_CHANNEL_ID` to this repository variables and redeploy, the broadcast functionallity should be available now.
