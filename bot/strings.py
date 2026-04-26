WELCOME_SUPERADMIN = "Welcome back. You have full system access."
WELCOME_ADMIN = "Welcome back. Your admin tools are ready."
WELCOME_USER = "Welcome back to MedLocum."
WELCOME_GUEST = "Welcome to MedLocum. Please send your access code to complete verification."
WELCOME_PENDING = (
    "Welcome to MedLocum.\n\n"
    "Your account is pending verification. To get started, you can reach out directly "
    "to one of our administrators below, or wait for your access code."
)
CODE_ACCEPTED = "Verification successful. You now have full access to the MedLocum platform."

MENU_ADMIN = "MedLocum Content Hub\n\nManage your content pipeline, team, and broadcasts from one place."
MENU_USER = "MedLocum Content Hub\n\nYou have full platform access."
MENU_PENDING = "MedLocum Content Hub\n\nYour account is pending verification.\nContact an administrator to receive your access code."

DRAFT_PROMPT = (
    "New Draft\n\n"
    "Send your post content now — text, formatting, and hashtags all supported.\n\n"
    "Tap Cancel to go back."
)

_SEP = "─" * 28

DRAFT_STEP1 = (
    "New Post\n"
    f"{_SEP}\n"
    "Step 1 of 2 — Subject\n\n"
    "Enter a headline for this post:"
)
DRAFT_STEP1_ERROR = (
    "New Post\n"
    f"{_SEP}\n"
    "Step 1 of 2 — Subject\n\n"
    "{error}\n\n"
    "Enter a headline for this post:"
)
DRAFT_STEP2 = (
    "New Post\n"
    f"{_SEP}\n"
    "{subject}\n"
    f"{_SEP}\n"
    "Step 2 of 2 — Body\n\n"
    "Send the post content — text, formatting, hashtags:"
)
DRAFT_PREVIEW = (
    "New Post — Preview\n"
    f"{_SEP}\n"
    "{subject}\n\n"
    "{body}\n"
    f"{_SEP}\n"
    "What would you like to do?"
)
DRAFT_SCHED_TYPE = (
    "New Post — Schedule\n"
    f"{_SEP}\n"
    "{subject}\n"
    f"{_SEP}\n"
    "Choose schedule type:"
)
DRAFT_TIME_PICK = (
    "New Post — Time\n"
    f"{_SEP}\n"
    "{subject}\n"
    "Recurring schedule\n"
    f"{_SEP}\n"
    "Choose posting time:"
)
DRAFT_CUSTOM_TIME = (
    "New Post — Custom Time\n"
    f"{_SEP}\n"
    "{subject}\n"
    f"{_SEP}\n"
    "Enter time in HH:MM format (24-hour):\n"
    "Example: 09:30"
)
DRAFT_CUSTOM_TIME_ERROR = (
    "New Post — Custom Time\n"
    f"{_SEP}\n"
    "{error}\n\n"
    "Enter time as HH:MM (e.g. 14:30):"
)
DRAFT_DAY_PICK = (
    "New Post — Days\n"
    f"{_SEP}\n"
    "{subject}\n"
    "Every day at {time_text}\n"
    f"{_SEP}\n"
    "Which days should this post run?"
)
DRAFT_DATETIME_PICK = (
    "New Post — Date & Time\n"
    f"{_SEP}\n"
    "{subject}\n"
    "One-time post\n"
    f"{_SEP}\n"
    "When should this post go live?\n\n"
    "Send date and time:\n"
    "DD/MM/YYYY HH:MM"
)
DRAFT_DATETIME_ERROR = (
    "New Post — Date & Time\n"
    f"{_SEP}\n"
    "{error}\n\n"
    "Send date and time:\n"
    "DD/MM/YYYY HH:MM"
)
DRAFT_TARGETS = (
    "New Post — Targets\n"
    f"{_SEP}\n"
    "{subject}\n"
    "{schedule_line}\n"
    f"{_SEP}\n"
    "Select where to send this post:"
)
DRAFT_NO_TARGETS = (
    "No connected groups or channels found.\n\n"
    "Add this bot as an admin to your channel or group first, "
    "then it will appear here automatically."
)
DRAFT_SAVED = "Saved to Drafts."
DRAFT_SCHEDULED_RECURRING = (
    "Scheduled\n\n"
    "{subject}\n"
    "Runs every {days_text} at {time_text}\n"
    "{target_count} destination(s)"
)
DRAFT_SCHEDULED_ONCE = (
    "Scheduled\n\n"
    "{subject}\n"
    "Posts on {datetime_text}\n"
    "{target_count} destination(s)"
)
DRAFT_REPORT_HEADER = "Broadcast Report\n" + _SEP + "\n"
DRAFT_REPORT_ROW_OK = "{title}"
DRAFT_REPORT_ROW_FAIL = "{title}\n   Error: {error}"
DRAFT_REPORT_FOOTER = "\n" + _SEP + "\nSent: {sent}  ·  Failed: {failed}"
DRAFT_NO_SELECTION = "Select at least one target."

SETTINGS_TEXT = (
    "Settings\n\n"
    "Timezone:   Africa/Lagos\n"
    "AI Review:  Enabled\n"
    "Storage:    Active\n"
    "Version:    1.4"
)
HELP_TEXT = (
    "MedLocum Content Bot — Commands\n\n"
    "/start      Open main menu\n"
    "/menu       Main menu\n"
    "/new        Create a new draft\n"
    "/content    Content library\n"
    "/users      Manage team\n"
    "/settings   Bot settings\n"
    "/admin      Control centre"
)
ADMIN_CODE_FOR_USER = "Verification code generated. Share this code with the user: {code}\n\nThis code expires in 10 minutes."
ONBOARD_SUCCESS = "Verification successful. You now have full access to the MedLocum content platform."
INVALID_CODE = "The verification code is incorrect. Please check the code and try again."
CODE_INVALID = INVALID_CODE
CODE_EXPIRED = "This verification code has expired. Please request a new code from an administrator."
PENDING_ACCESS = "Your account is pending verification. This feature is restricted until you are onboarded."
ACCOUNT_DEACTIVATED = "Your account has been deactivated. Please contact a system administrator."
YOU_WERE_PROMOTED = "You have been promoted to Admin. You now have access to moderation and content management tools."
YOU_WERE_PROMOTED_SUPERADMIN = "You have been promoted to Super Admin. You now have full system access."
YOU_WERE_DEMOTED = "Your role has been updated to Admin."
YOU_WERE_REMOVED = "Your access to the platform has been revoked."
CANNOT_DEMOTE_OWNER = "The system owner cannot be demoted or removed."
ADMIN_PROMOTED_USER = "User {name} has been promoted to Admin by {actor}."
ADMIN_PROMOTED_SUPERADMIN = "User {name} has been promoted to Super Admin by {actor}."
NEW_USER_NOTIFICATION = (
    "New user: {name} (@{username})\n"
    "User ID: {user_id}\n\n"
    "Tap below to generate a verification code."
)
ADMIN_PANEL_HEADER = "MedLocum Control Centre\nBucket: {bucket}"
BUCKET_TITLE = "{bucket} Bucket"
ITEM_VIEW = "Content Item\n\nBucket: {bucket}\n\n{text}"
BUCKET_EMPTY = "This bucket currently contains no items."
ITEM_DETAIL_HEADER = "Content Item\n\nID: {id}\nBucket: {bucket}"
SCHEDULE_CONFIRMED = "Scheduled for {time} ({recurrence})."
BROADCAST_CONFIRMED = "Broadcast initiated for {count} targets."
BROADCAST_STARTED = "Broadcast scheduled successfully."
BROADCAST_SKIP_DEDUP = "Broadcast skipped for {target}: duplicate content detected."
TONE_FLAG_WARNING = "Tone Advisory: This content has been flagged as potentially unprofessional (Score: {score}). Manual review recommended."
PUBLISH_FAILED_MAX_RETRIES = "Scheduled post {id} failed to publish after maximum retry attempts."
SCHEDULER_RESTORED = "System Recovery: {count} scheduled tasks restored to the active queue."
BOT_ONLINE = "MedLocum Bot is now online."
BOT_SHUTDOWN = "MedLocum Bot is shutting down."
MEDICAL_DISCLAIMER = "Disclaimer: This content is for informational purposes only. Always consult a qualified medical professional for clinical decisions."
STORAGE_UPLOAD_SUCCESS = "File archived to the primary storage channel."
STORAGE_DELETE_CONFIRM = "File permanently removed from the storage channel."
INVALID_ACTION = "This action could not be completed. Please refresh the interface."
MODERATION_RESOLVED = "Moderation status updated: {res}"
RATE_LIMITED = "Rate limit exceeded. Please wait one minute before trying again."
AI_FEATURE_DISABLED = "AI features are not active. Add API keys to enable."

PERSONA_LIST_HEADER = (
    "Personas\n\n"
    "The active persona signs every broadcast post.\n"
    "Only one persona can be active at a time."
)
PERSONA_ENTER_NAME = (
    "New Persona\n\n"
    "Send the persona name — or name and title separated by  |  \n\n"
    "Examples:\n"
    "  Steve\n"
    "  Zara | MedLocum Senior Editor\n"
    "  Dr. Mark | Clinical Content Lead"
)
PERSONA_CREATED = "Persona '{name}' created. Tap Activate to make it the active voice for broadcasts."
PERSONA_ACTIVATED = "Persona activated. All future broadcasts will be signed with this persona."
PERSONA_DELETED = "Persona removed."
PERSONA_DETAIL = (
    "{name}\n"
    "Title:      {title}\n"
    "Signature:  {signature}\n"
    "Status:     {status}"
)

FAQ_LIST_HEADER = (
    "Auto-Reply\n\n"
    "When a group member sends a message containing a trigger phrase, "
    "the bot replies instantly with the saved response."
)
FAQ_ENTER_TRIGGER = (
    "New Auto-Reply — Step 1 of 2\n\n"
    "Send the trigger phrase (what members will type).\n\n"
    "Examples:\n"
    "  locum rates\n"
    "  how to apply\n"
    "  cme credits"
)
FAQ_ENTER_RESPONSE = (
    "New Auto-Reply — Step 2 of 2\n\n"
    "Now send the reply the bot should send when that phrase is detected."
)
FAQ_CREATED = "Auto-reply saved for trigger: '{trigger}'"
FAQ_DELETED = "Auto-reply removed."
FAQ_DETAIL = (
    "Auto-Reply\n\n"
    "Trigger:    {trigger}\n"
    "Match:      {match}\n"
    "Status:     {status}\n\n"
    "Response preview:\n{response}"
)

WELCOME_NONE_SET = (
    "Welcome Message\n\n"
    "No welcome message configured yet.\n"
    "Set one to greet new members automatically."
)
WELCOME_CURRENT = (
    "Welcome Message\n\n"
    "Status:  {status}\n\n"
    "Preview:\n{preview}"
)
WELCOME_ENTER_MESSAGE = (
    "Welcome Message\n\n"
    "Send the welcome text. You can use:\n"
    "  {name}      — member's display name\n"
    "  {username}  — @handle or name\n"
    "  {chat}      — channel/group title"
)
WELCOME_SAVED = "Welcome message saved and active."
WELCOME_ENABLED = "Welcome message enabled."
WELCOME_DISABLED = "Welcome message paused."

GROUP_SETTINGS_LIST = (
    "Groups & Channels\n\n"
    "Select a group or channel to configure its welcome message, "
    "moderation rules, and auto-mod settings."
)
GROUP_PANEL_EMPTY = (
    "No groups or channels connected yet.\n\n"
    "Add the bot to a group or channel as an admin and it will appear here."
)
GROUP_PANEL = (
    "{name}\n"
    "Moderation:   {mod}\n"
    "Link filter:  {links}\n"
    "Warn limit:   {warn_limit} warnings — removed\n"
    "Banned words: {kw_count} term(s)\n\n"
    "Welcome msg:  {welcome}\n"
    "Preview:      {welcome_preview}"
)
GROUP_KW_ENTER = (
    "Banned Words\n\n"
    "Send a comma-separated list of words to auto-delete and warn on.\n\n"
    "Example:  spam, casino, crypto, click here\n\n"
    "Send a single dash  -  to clear the list."
)
GROUP_KW_SAVED = "Banned word list updated ({count} term(s) active)."

BROADCAST_SENT = "Sent to {count} channel(s) as {persona}."
BROADCAST_NO_PERSONA = "Sent to {count} channel(s)."
STATS_TEXT = (
    "Content Stats\n\n"
    "Drafts:      {drafts}\n"
    "Scheduled:   {scheduled}\n"
    "Published:   {published}\n"
    "Archived:    {archive}\n\n"
    "Team:        {users} members\n"
    "Active Persona: {persona}"
)
