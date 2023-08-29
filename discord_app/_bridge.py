# on_error
  # type, exc, _ = exc_info()
  # if type is NotImplementedError:
  #   _log.warn(f'ignoring unhandled {event}')
  # elif type is not RawEventException:
  #   print_exception(exc)

# on_socket_event_type
  # self.event_counter[event_type] = self.event_counter.get(event_type, 0) + 1

# on_disconnect
  # if self.is_closed():
  #   n = len(self.event_counter)
  #   ordered = sorted(
  #     self.event_counter, key=self.event_counter.get, reverse=True
  #   ) + [''] * (2 - n % 2)
  #   if n % 2:
  #     self.event_counter[''] = 0
  #   report = '-' * 34 + 'EVENT REPORT' + '-' * 34 + '\n' + \
  #     '| TYPE:                              # ' * 2 + ' |\n' + \
  #     '\n'.join(
  #       '| ' + ' | '.join(
  #         f'{ordered[(n + 1) // 2 * c + r]:30s} ' \
  #         f'{self.event_counter[ordered[(n + 1) // 2 * c + r]]:5d}'
  #       for c in range(2)) + '  |'
  #     for r in range((n + 1) // 2)) + '\n' + '-' * 80
  #   print(report)

from asyncio import run_coroutine_threadsafe as submit
from concurrent.futures import Future
from datetime import datetime
from logging import DEBUG
from threading import Thread
from typing import Coroutine, NamedTuple, Sequence

from discord_app import (
  DRawAppCommandPermissionsUpdateEvent, DInteraction, DCommand, DContextMenu,
  DAutoModRule, DAutoModAction, DGuildChannel, DThread, DGroupChannel,
  DPrivateChannel, DTextChannel, DDMChannel, DUser, DMember, DRawTypingEvent,
  DGuild, DEmoji, DGuildSticker, DAuditLogEntry, DInvite, DIntegration,
  DRawIntegrationDeleteEvent, DRawMemberRemoveEvent, DMessage,
  DRawMessageUpdateEvent, DRawMessageDeleteEvent, DRawBulkMessageDeleteEvent,
  DReaction, DRawReactionActionEvent, DRawReactionClearEvent,
  DRawReactionClearEmojiEvent, DRole, DScheduledEvent, DStageInstance,
  DRawThreadUpdateEvent, DRawThreadDeleteEvent, DThreadMember,
  DRawThreadMembersUpdate, DVoiceState,
  DClient, DIntents, DStatus, DGame,
  QObject, pyqtSignal,
  TOKEN, Signal, Signal_, Signal__, Signal___
)

class ErrorSource(NamedTuple):
  event: str
  args: list
  kwargs: dict

class DSignals(QObject):
  
################################ App Commands ################################

  on_raw_app_command_permissions_update: Signal_[DRawAppCommandPermissionsUpdateEvent] = pyqtSignal(object)
  '''
  Called when application command permissions are updated.
  New in version 2.0.
  
  ## Parameters
  - payload - The raw event payload data.
  '''

  on_app_command_completion: Signal__[DInteraction, DCommand | DContextMenu] = pyqtSignal(object, object)
  '''
  Called when a app_commands.Command or app_commands.ContextMenu has successfully completed without error.
  New in version 2.0.

  ## Parameters
  - interaction - The interaction of the command.
  - command - The command that completed successfully
  '''
  
################################ AutoMod ################################

  on_automod_rule_create: Signal_[DAutoModRule] = pyqtSignal(object)
  '''
  Called when a AutoModRule is created. You must have manage_guild to receive this.
  This requires Intents.auto_moderation_configuration to be enabled.
  New in version 2.0.

  ## Parameters
  - rule - The rule that was created.
  '''

  on_automod_rule_update: Signal_[DAutoModRule] = pyqtSignal(object)
  '''
  Called when a AutoModRule is updated. You must have manage_guild to receive this.
  This requires Intents.auto_moderation_configuration to be enabled.
  New in version 2.0.

  ## Parameters
  - rule - The rule that was updated.
  '''

  on_automod_rule_delete: Signal_[DAutoModRule] = pyqtSignal(object)
  '''
  Called when a AutoModRule is deleted. You must have manage_guild to receive this.
  This requires Intents.auto_moderation_configuration to be enabled.
  New in version 2.0.

  ## Parameters
  - rule - The rule that was deleted.
  '''

  on_automod_action: Signal_[DAutoModAction] = pyqtSignal(object)
  '''
  Called when a AutoModAction is created/performed. You must have manage_guild to receive this.
  This requires Intents.auto_moderation_execution to be enabled.
  New in version 2.0.

  ## Parameters
  - execution - The rule execution that was performed.
  '''
  
################################ Channels ################################

  on_guild_channel_delete: Signal_[DGuildChannel] = pyqtSignal(object)
  '''
  Called whenever a guild channel is deleted.
  Note that you can get the guild from guild.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - channel - The guild channel that got created or deleted.
  '''

  on_guild_channel_create: Signal_[DGuildChannel] = pyqtSignal(object)
  '''
  Called whenever a guild channel is created.
  Note that you can get the guild from guild.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - channel - The guild channel that got created or deleted.
  '''

  on_guild_channel_update: Signal__[DGuildChannel, DGuildChannel] = pyqtSignal(object, object)
  '''
  Called whenever a guild channel is updated. e.g. changed name, topic, permissions.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - before - The updated guild channel's old info.
  - after - The updated guild channel's new info.
  '''

  on_guild_channel_pins_update: Signal__[DGuildChannel | DThread, datetime | None] = pyqtSignal(object, object)
  '''
  Called whenever a message is pinned or unpinned from a guild channel.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - channel - The guild channel that had its pins updated.
  - last_pin - The latest message that was pinned as an aware datetime in UTC. Could be None.
  '''

  on_private_channel_update: Signal__[DGroupChannel, DGroupChannel] = pyqtSignal(object, object)
  '''
  Called whenever a private group DM is updated. e.g. changed name or topic.
  This requires Intents.messages to be enabled.

  ## Parameters
  - before - The updated group channel's old info.
  - after - The updated group channel's new info.
  '''

  on_private_channel_pins_update: Signal__[DPrivateChannel, datetime | None] = pyqtSignal(object, object)
  '''
  Called whenever a message is pinned or unpinned from a private channel.

  ## Parameters
  - channel - The private channel that had its pins updated.
  - last_pin - The latest message that was pinned as an aware datetime in UTC. Could be None.
  '''

  on_typing: Signal___[DTextChannel | DGroupChannel | DDMChannel, DUser | DMember, datetime] = pyqtSignal(object, object, object)
  '''
  Called when someone begins typing a message.
  The channel parameter can be a abc.Messageable instance. Which could either be TextChannel, GroupChannel, or DMChannel.
  If the channel is a TextChannel then the user parameter is a Member, otherwise it is a User.
  If the channel or user could not be found in the internal cache this event will not be called, you may use on_raw_typing() instead.
  This requires Intents.typing to be enabled.

  ## Parameters
  - channel - The location where the typing originated from.
  - user - The user that started typing.
  - when - When the typing started as an aware datetime in UTC.
  '''

  on_raw_typing: Signal_[DRawTypingEvent] = pyqtSignal(object)
  '''
  Called when someone begins typing a message. Unlike on_typing() this is called regardless of the channel and user being in the internal cache.
  This requires Intents.typing to be enabled.
  New in version 2.0.

  ## Parameters
  - payload - The raw event payload data.
  '''
  
################################ Connection ################################

  on_connect: Signal = pyqtSignal(object)
  '''
  Called when the client has successfully connected to Discord. This is not the same as the client being fully prepared, see on_ready() for that.
  The warnings on on_ready() also apply.
  '''

  on_disconnect: Signal = pyqtSignal(object)
  '''
  Called when the client has disconnected from Discord, or a connection attempt to Discord has failed. This could happen either through the internet being disconnected, explicit calls to close, or Discord terminating the connection one way or the other.
  This function can be called many times without a corresponding on_connect() call.
  '''

  on_shard_connect: Signal_[int] = pyqtSignal(object)
  '''
  Similar to on_connect() except used by AutoShardedClient to denote when a particular shard ID has connected to Discord.
  New in version 1.4.

  ## Parameters
  - shard_id - The shard ID that has connected.
  '''

  on_shard_disconnect: Signal_[int] = pyqtSignal(object)
  '''
  Similar to on_disconnect() except used by AutoShardedClient to denote when a particular shard ID has disconnected from Discord.
  New in version 1.4.

  ## Parameters
  - shard_id - The shard ID that has disconnected.
  '''
  
################################ Debug ################################

  on_error: Signal_[ErrorSource] = pyqtSignal(object)
  '''
  Usually when an event raises an uncaught exception, a traceback is logged to stderr and the exception is ignored. If you want to change this behaviour and handle the exception for whatever reason yourself, this event can be overridden. Which, when done, will suppress the default action of printing the traceback.
  The information of the exception raised and the exception itself can be retrieved with a standard call to sys.exc_info().
  on_error will only be dispatched to Client.event().
  It will not be received by Client.wait_for(), or, if used, Bots listeners such as listen() or listener().
  Changed in version 2.0: The traceback is now logged rather than printed.

  ## Parameters
  - event - The name of the event that raised the exception.
  - args - The positional arguments for the event that raised the exception.
  - kwargs - The keyword arguments for the event that raised the exception.
  '''

  on_socket_event_type: Signal_[str] = pyqtSignal(object)
  '''
  Called whenever a websocket event is received from the WebSocket.
  This is mainly useful for logging how many events you are receiving from the Discord gateway.
  New in version 2.0.

  ## Parameters
  - event_type - The event type from Discord that is received, e.g. 'READY'elf.event_counter[event_type.
  '''

  on_socket_raw_receive: Signal_[str] = pyqtSignal(object)
  '''
  Called whenever a message is completely received from the WebSocket, before it's processed and parsed. This event is always dispatched when a complete message is received and the passed data is not parsed in any way.
  This is only really useful for grabbing the WebSocket stream and debugging purposes.
  This requires setting the enable_debug_events setting in the Client.
  This is only for the messages received from the client WebSocket. The voice WebSocket will not trigger this event.

  ## Parameters
  - msg - The message passed in from the WebSocket library.
  '''

  on_socket_raw_send: Signal_[bytes | str] = pyqtSignal(object)
  '''
  Called whenever a send operation is done on the WebSocket before the message is sent. The passed parameter is the message that is being sent to the WebSocket.
  This is only really useful for grabbing the WebSocket stream and debugging purposes.
  This requires setting the enable_debug_events setting in the Client.
  This is only for the messages sent from the client WebSocket. The voice WebSocket will not trigger this event.

  ## Parameters
  - payload - The message that is about to be passed on to the WebSocket library. It can be bytes to denote a binary message or str to denote a regular text message.
  '''
  
################################ Gateway ################################

  on_ready: Signal = pyqtSignal(object)
  '''
  Called when the client is done preparing the data received from Discord. Usually after login is successful and the Client.guilds and co. are filled up.
  This function is not guaranteed to be the first event called. Likewise, this function is not guaranteed to only be called once. This library implements reconnection logic and thus will end up calling this event whenever a RESUME request fails.
  '''

  on_resumed: Signal = pyqtSignal(object)
  '''
  Called when the client has resumed a session.
  '''

  on_shard_ready: Signal_[int] = pyqtSignal(object)
  '''
  Similar to on_ready() except used by AutoShardedClient to denote when a particular shard ID has become ready.

  ## Parameters
  - shard_id - The shard ID that is ready.
  '''

  on_shard_resumed: Signal_[int] = pyqtSignal(object)
  '''
  Similar to on_resumed() except used by AutoShardedClient to denote when a particular shard ID has resumed a session.
  New in version 1.4.

  ## Parameters
  - shard_id - The shard ID that has resumed.
  '''
  
################################ Guilds ################################

  on_guild_available: Signal_[DGuild] = pyqtSignal(object)
  '''
  Called when a guild becomes available. The guild must have existed in the Client.guilds cache.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - guild - The Guild that has changed availability.
  '''

  on_guild_unavailable: Signal_[DGuild] = pyqtSignal(object)
  '''
  Called when a guild becomes unavailable. The guild must have existed in the Client.guilds cache.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - guild - The Guild that has changed availability.
  '''

  on_guild_join: Signal_[DGuild] = pyqtSignal(object)
  '''
  Called when a Guild is either created by the Client or when the Client joins a guild.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - guild - The guild that was joined.
  '''

  on_guild_remove: Signal_[DGuild] = pyqtSignal(object)
  '''
  Called when a Guild is removed from the Client.
  This happens through, but not limited to, these circumstances:
  - The client got banned.
  - The client got kicked.
  - The client left the guild.
  - The client or the guild owner deleted the guild.

  In order for this event to be invoked then the Client must have been part of the guild to begin with. (i.e. it is part of Client.guilds)
  This requires Intents.guilds to be enabled.

  ## Parameters
  - guild - The guild that got removed.
  '''

  on_guild_update: Signal__[DGuild, DGuild] = pyqtSignal(object, object)
  '''
  Called when a Guild updates, for example:
  - Changed name
  - Changed AFK channel
  - Changed AFK timeout
  - etc

  This requires Intents.guilds to be enabled.

  ## Parameters
  - before - The guild prior to being updated.
  - after - The guild after being updated.
  '''

  on_guild_emojis_update: Signal___[DGuild, Sequence[DEmoji], Sequence[DEmoji]] = pyqtSignal(object, object, object)
  '''
  Called when a Guild adds or removes Emoji.
  This requires Intents.emojis_and_stickers to be enabled.

  ## Parameters
  - guild - The guild who got their emojis updated.
  - before - A list of emojis before the update.
  - after - A list of emojis after the update.
  '''

  on_guild_stickers_update: Signal___[DGuild, Sequence[DGuildSticker], Sequence[DGuildSticker]] = pyqtSignal(object, object, object)
  '''
  Called when a Guild updates its stickers.
  This requires Intents.emojis_and_stickers to be enabled.
  New in version 2.0.

  ## Parameters
  - guild - The guild who got their stickers updated.
  - before - A list of stickers before the update.
  - after - A list of stickers after the update.
  '''

  on_audit_log_entry_create: Signal_[DAuditLogEntry] = pyqtSignal(object)
  '''
  Called when a Guild gets a new audit log entry. You must have view_audit_log to receive this.
  This requires Intents.moderation to be enabled.
  New in version 2.2.
  Audit log entries received through the gateway are subject to data retrieval from cache rather than REST. This means that some data might not be present when you expect it to be. For example, the AuditLogEntry.target attribute will usually be a discord.Object and the AuditLogEntry.user attribute will depend on user and member cache.
  To get the user ID of entry, AuditLogEntry.user_id can be used instead.

  ## Parameters
  - entry - The audit log entry that was created.
  '''

  on_invite_create: Signal_[DInvite] = pyqtSignal(object)
  '''
  Called when an Invite is created. You must have manage_channels to receive this.
  New in version 1.3.
  There is a rare possibility that the Invite.guild and Invite.channel attributes will be of Object rather than the respective models.
  This requires Intents.invites to be enabled.

  ## Parameters
  - invite - The invite that was created.
  '''

  on_invite_delete: Signal_[DInvite] = pyqtSignal(object)
  '''
  Called when an Invite is deleted. You must have manage_channels to receive this.
  New in version 1.3.
  There is a rare possibility that the Invite.guild and Invite.channel attributes will be of Object rather than the respective models.
  Outside of those two attributes, the only other attribute guaranteed to be filled by the Discord gateway for this event is Invite.code.
  This requires Intents.invites to be enabled.

  ## Parameters
  - invite - The invite that was deleted.
  '''
  
################################ Integrations ################################

  on_integration_create: Signal_[DIntegration] = pyqtSignal(object)
  '''
  Called when an integration is created.
  This requires Intents.integrations to be enabled.
  New in version 2.0.

  ## Parameters
  - integration - The integration that was created.
  '''

  on_integration_update: Signal_[DIntegration] = pyqtSignal(object)
  '''
  Called when an integration is updated.
  This requires Intents.integrations to be enabled.
  New in version 2.0.

  ## Parameters
  - integration - The integration that was updated.
  '''

  on_guild_integrations_update: Signal_[DGuild] = pyqtSignal(object)
  '''
  Called whenever an integration is created, modified, or removed from a guild.
  This requires Intents.integrations to be enabled.
  New in version 1.4.

  ## Parameters
  - guild - The guild that had its integrations updated.
  '''

  on_webhooks_update: Signal_[DGuildChannel] = pyqtSignal(object)
  '''
  Called whenever a webhook is created, modified, or removed from a guild channel.
  This requires Intents.webhooks to be enabled.

  ## Parameters
  - channel - The channel that had its webhooks updated.
  '''

  on_raw_integration_delete: Signal_[DRawIntegrationDeleteEvent] = pyqtSignal(object)
  '''
  Called when an integration is deleted.
  This requires Intents.integrations to be enabled.
  New in version 2.0.

  ## Parameters
  - payload - The raw event payload data.
  '''
  
################################ Interactions ################################

  on_interaction: Signal_[DInteraction] = pyqtSignal(object)
  '''
  Called when an interaction happened.
  This currently happens due to slash command invocations or components being used.
  This is a low level function that is not generally meant to be used. If you are working with components, consider using the callbacks associated with the View instead as it provides a nicer user experience.
  New in version 2.0.

  ## Parameters
  - interaction - The interaction data.
  '''
  
################################ Members ################################

  on_member_join: Signal_[DMember] = pyqtSignal(object)
  '''
  Called when a Member joins a Guild.
  This requires Intents.members to be enabled.

  ## Parameters
  - member - The member who joined.
  '''

  on_member_remove: Signal_[DMember] = pyqtSignal(object)
  '''
  Called when a Member leaves a Guild.
  If the guild or member could not be found in the internal cache this event will not be called, you may use on_raw_member_remove() instead.
  This requires Intents.members to be enabled.

  ## Parameters
  - member - The member who left.
  '''

  on_raw_member_remove: Signal_[DRawMemberRemoveEvent] = pyqtSignal(object)
  '''
  Called when a Member leaves a Guild.
  Unlike on_member_remove() this is called regardless of the guild or member being in the internal cache.
  This requires Intents.members to be enabled.
  New in version 2.0.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_member_update: Signal__[DMember, DMember] = pyqtSignal(object, object)
  '''
  Called when a Member updates their profile.
  This is called when one or more of the following things change:
  - nickname
  - roles
  - pending
  - timeout
  - guild avatar
  - flags

  Due to a Discord limitation, this event is not dispatched when a member's timeout expires.
  This requires Intents.members to be enabled.

  ## Parameters
  - before - The updated member's old info.
  - after - The updated member's updated info.
  '''

  on_user_update: Signal__[DUser, DUser] = pyqtSignal(object, object)
  '''
  Called when a User updates their profile.
  This is called when one or more of the following things change:
  - avatar
  - username
  - discriminator

  This requires Intents.members to be enabled.

  ## Parameters
  - before - The updated user's old info.
  - after - The updated user's updated info.
  '''

  on_member_ban: Signal__[DGuild, DUser | DMember] = pyqtSignal(object, object)
  '''
  Called when user gets banned from a Guild.
  This requires Intents.moderation to be enabled.

  ## Parameters
  - guild - The guild the user got banned from.
  - user - The user that got banned. Can be either User or Member depending if the user was in the guild or not at the time of removal.
  '''

  on_member_unban: Signal__[DGuild, DUser] = pyqtSignal(object, object)
  '''
  Called when a User gets unbanned from a Guild.
  This requires Intents.moderation to be enabled.

  ## Parameters
  - guild - The guild the user got unbanned from.
  - user - The user that got unbanned.
  '''

  on_presence_update: Signal__[DMember, DMember] = pyqtSignal(object, object)
  '''
  Called when a Member updates their presence.
  This is called when one or more of the following things change:
  - status
  - activity

  This requires Intents.presences and Intents.members to be enabled.
  New in version 2.0.

  ## Parameters
  - before - The updated member's old info.
  - after - The updated member's updated info.
  '''
  
################################ Messages ################################

  on_message: Signal_[DMessage] = pyqtSignal(object)
  '''
  Called when a Message is created and sent.
  This requires Intents.messages to be enabled.
  Your bot's own messages and private messages are sent through this event. This can lead cases of 'recursion' depending on how your bot was programmed. If you want the bot to not reply to itself, consider checking the user IDs. Note that Bot does not have this problem.

  ## Parameters
  - message - The current message.
  '''

  on_message_edit: Signal__[DMessage, DMessage] = pyqtSignal(object, object)
  '''
  Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds.
  If this occurs increase the max_messages parameter or use the on_raw_message_edit() event instead.
  The following non-exhaustive cases trigger this event:
  - A message has been pinned or unpinned.
  - The message content has been changed.
  - The message has received an embed.
    - For performance reasons, the embed server does not do this in a “consistent” manner.
  - The message's embeds were suppressed or unsuppressed.
  - A call message has received an update to its participants or ending time.

  This requires Intents.messages to be enabled.

  ## Parameters
  - before - The previous version of the message.
  - after - The current version of the message.
  '''

  on_message_delete: Signal_[DMessage] = pyqtSignal(object)
  '''
  Called when a message is deleted. If the message is not found in the internal message cache, then this event will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds.
  If this occurs increase the max_messages parameter or use the on_raw_message_delete() event instead.
  This requires Intents.messages to be enabled.

  ## Parameters
  - message - The deleted message.
  '''

  on_bulk_message_delete: Signal_[list[DMessage]] = pyqtSignal(object)
  '''
  Called when messages are bulk deleted. If none of the messages deleted are found in the internal message cache, then this event will not be called. If individual messages were not found in the internal message cache, this event will still be called, but the messages not found will not be included in the messages list. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds.
  If this occurs increase the max_messages parameter or use the on_raw_bulk_message_delete() event instead.
  This requires Intents.messages to be enabled.

  ## Parameters
  - messages - The messages that have been deleted.
  '''

  on_raw_message_edit: Signal_[DRawMessageUpdateEvent] = pyqtSignal(object)
  '''
  Called when a message is edited. Unlike on_message_edit(), this is called regardless of the state of the internal message cache.
  If the message is found in the message cache, it can be accessed via RawMessageUpdateEvent.cached_message. The cached message represents the message before it has been edited. For example, if the content of a message is modified and triggers the on_raw_message_edit() coroutine, the RawMessageUpdateEvent.cached_message will return a Message object that represents the message before the content was modified.
  Due to the inherently raw nature of this event, the data parameter coincides with the raw data given by the gateway.
  Since the data payload can be partial, care must be taken when accessing stuff in the dictionary. One example of a common case of partial data is when the 'content' key is inaccessible. This denotes an “embed” only edit, which is an edit in which only the embeds are updated by the Discord embed server.
  This requires Intents.messages to be enabled.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_raw_message_delete: Signal_[DRawMessageDeleteEvent] = pyqtSignal(object)
  '''
  Called when a message is deleted. Unlike on_message_delete(), this is called regardless of the message being in the internal message cache or not.
  If the message is found in the message cache, it can be accessed via RawMessageDeleteEvent.cached_message
  This requires Intents.messages to be enabled.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_raw_bulk_message_delete: Signal_[DRawBulkMessageDeleteEvent] = pyqtSignal(object)
  '''
  Called when a bulk delete is triggered. Unlike on_bulk_message_delete(), this is called regardless of the messages being in the internal message cache or not.
  If the messages are found in the message cache, they can be accessed via RawBulkMessageDeleteEvent.cached_messages
  This requires Intents.messages to be enabled.

  ## Parameters
  - payload - The raw event payload data.
  '''
  
################################ Reactions ################################

  on_reaction_add: Signal__[DReaction, DMember | DUser] = pyqtSignal(object, object)
  '''
  Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead.
  To get the Message being reacted, access it via Reaction.message.
  This requires Intents.reactions to be enabled.
  This doesn't require Intents.members within a guild context, but due to Discord not providing updated user information in a direct message it's required for direct messages to receive this event. Consider using on_raw_reaction_add() if you need this and do not otherwise want to enable the members intent.

  ## Parameters
  - reaction - The current state of the reaction.
  - user - The user who added the reaction.
  '''

  on_reaction_remove: Signal__[DReaction, DMember | DUser] = pyqtSignal(object, object)
  '''
  Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called.
  To get the message being reacted, access it via Reaction.message.
  This requires both Intents.reactions and Intents.members to be enabled.
  Consider using on_raw_reaction_remove() if you need this and do not want to enable the members intent.

  ## Parameters
  - reaction - The current state of the reaction.
  - user - The user whose reaction was removed.
  '''

  on_reaction_clear: Signal__[DMessage, list[DReaction]] = pyqtSignal(object, object)
  '''
  Called when a message has all its reactions removed from it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_clear() instead.
  This requires Intents.reactions to be enabled.

  ## Parameters
  - message - The message that had its reactions cleared.
  - reactions - The reactions that were removed.
  '''

  on_reaction_clear_emoji: Signal_[DReaction] = pyqtSignal(object)
  '''
  Called when a message has a specific reaction removed from it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_clear_emoji() instead.
  This requires Intents.reactions to be enabled.
  New in version 1.3.

  ## Parameters
  - reaction - The reaction that got cleared.
  '''

  on_raw_reaction_add: Signal_[DRawReactionActionEvent] = pyqtSignal(object)
  '''
  Called when a message has a reaction added. Unlike on_reaction_add(), this is called regardless of the state of the internal message cache.
  This requires Intents.reactions to be enabled.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_raw_reaction_remove: Signal_[DRawReactionActionEvent] = pyqtSignal(object)
  '''
  Called when a message has a reaction removed. Unlike on_reaction_remove(), this is called regardless of the state of the internal message cache.
  This requires Intents.reactions to be enabled.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_raw_reaction_clear: Signal_[DRawReactionClearEvent] = pyqtSignal(object)
  '''
  Called when a message has all its reactions removed. Unlike on_reaction_clear(), this is called regardless of the state of the internal message cache.
  This requires Intents.reactions to be enabled.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_raw_reaction_clear_emoji: Signal_[DRawReactionClearEmojiEvent] = pyqtSignal(object)
  '''
  Called when a message has a specific reaction removed from it. Unlike on_reaction_clear_emoji() this is called regardless of the state of the internal message cache.
  This requires Intents.reactions to be enabled.
  New in version 1.3.

  ## Parameters
  - payload - The raw event payload data.
  '''
  
################################ Roles ################################

  on_guild_role_create: Signal_[DRole] = pyqtSignal(object)
  '''
  Called when a Guild creates a new Role.
  To get the guild it belongs to, use Role.guild.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - role - The role that was created or deleted.
  '''

  on_guild_role_delete: Signal_[DRole] = pyqtSignal(object)
  '''
  Called when a Guild deletes a Role.
  To get the guild it belongs to, use Role.guild.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - role - The role that was created or deleted.
  '''

  on_guild_role_update: Signal__[DRole, DRole] = pyqtSignal(object, object)
  '''
  Called when a Role is changed guild-wide.
  This requires Intents.guilds to be enabled.

  ## Parameters
  - before - The updated role's old info.
  - after - The updated role's updated info.
  '''

############################ Scheduled Events ############################

  on_scheduled_event_create: Signal_[DScheduledEvent] = pyqtSignal(object)
  '''
  Called when a ScheduledEvent is created.
  This requires Intents.guild_scheduled_events to be enabled.
  New in version 2.0.

  ## Parameters
  - event - The scheduled event that was created or deleted.
  '''

  on_scheduled_event_delete: Signal_[DScheduledEvent] = pyqtSignal(object)
  '''
  Called when a ScheduledEvent is deleted.
  This requires Intents.guild_scheduled_events to be enabled.
  New in version 2.0.

  ## Parameters
  - event - The scheduled event that was created or deleted.
  '''

  on_scheduled_event_update: Signal__[DScheduledEvent, DScheduledEvent] = pyqtSignal(object, object)
  '''
  Called when a ScheduledEvent is updated.
  This requires Intents.guild_scheduled_events to be enabled.
  The following, but not limited to, examples illustrate when this event is called:
  - The scheduled start/end times are changed.
  - The channel is changed.
  - The description is changed.
  - The status is changed.
  - The image is changed.

  New in version 2.0.

  ## Parameters
  - before - The scheduled event before the update.
  - after - The scheduled event after the update.
  '''

  on_scheduled_event_user_add: Signal__[DScheduledEvent, DUser] = pyqtSignal(object, object)
  '''
  Called when a user is added from a ScheduledEvent.
  This requires Intents.guild_scheduled_events to be enabled.
  New in version 2.0.

  ## Parameters
  - event - The scheduled event that the user was added or removed from.
  - user -The user that was added or removed.
  '''

  on_scheduled_event_user_remove: Signal__[DScheduledEvent, DUser] = pyqtSignal(object, object)
  '''
  Called when a user is removed from a ScheduledEvent.
  This requires Intents.guild_scheduled_events to be enabled.
  New in version 2.0.

  ## Parameters
  - event - The scheduled event that the user was added or removed from.
  - user - The user that was added or removed.
  '''
  
################################ Stages ################################

  on_stage_instance_create: Signal_[DStageInstance] = pyqtSignal(object)
  '''
  Called when a StageInstance is created for a StageChannel.
  New in version 2.0.

  ## Parameters
  - stage_instance - The stage instance that was created or deleted.
  '''

  on_stage_instance_delete: Signal_[DStageInstance] = pyqtSignal(object)
  '''
  Called when a StageInstance is deleted for a StageChannel.
  New in version 2.0.

  ## Parameters
  - stage_instance - The stage instance that was created or deleted.
  '''

  on_stage_instance_update: Signal__[DStageInstance, DStageInstance] = pyqtSignal(object, object)
  '''
  Called when a StageInstance is updated.
  The following, but not limited to, examples illustrate when this event is called:
  - The topic is changed.
  - The privacy level is changed.

  New in version 2.0.

  ## Parameters
  - before - The stage instance before the update.
  - after - The stage instance after the update.
  '''
  
################################ Threads ################################

  on_thread_create: Signal_[DThread] = pyqtSignal(object)
  '''
  Called whenever a thread is created.
  Note that you can get the guild from Thread.guild.
  This requires Intents.guilds to be enabled.
  New in version 2.0.

  ## Parameters
  - thread - The thread that was created.
  '''

  on_thread_join: Signal_[DThread] = pyqtSignal(object)
  '''
  Called whenever a thread is joined.
  Note that you can get the guild from Thread.guild.
  This requires Intents.guilds to be enabled.
  New in version 2.0.

  ## Parameters
  - thread - The thread that got joined.
  '''

  on_thread_update: Signal__[DThread, DThread] = pyqtSignal(object, object)
  '''
  Called whenever a thread is updated. If the thread could not be found in the internal cache this event will not be called. Threads will not be in the cache if they are archived.
  If you need this information use on_raw_thread_update() instead.
  This requires Intents.guilds to be enabled.
  New in version 2.0.

  ## Parameters
  - before - The updated thread's old info.
  - after - The updated thread's new info.
  '''

  on_thread_remove: Signal_[DThread] = pyqtSignal(object)
  '''
  Called whenever a thread is removed. This is different from a thread being deleted.
  Note that you can get the guild from Thread.guild.
  This requires Intents.guilds to be enabled.
  Due to technical limitations, this event might not be called as soon as one expects. Since the library tracks thread membership locally, the API only sends updated thread membership status upon being synced by joining a thread.
  New in version 2.0.

  ## Parameters
  - thread - The thread that got removed.
  '''

  on_thread_delete: Signal_[DThread] = pyqtSignal(object)
  '''
  Called whenever a thread is deleted. If the thread could not be found in the internal cache this event will not be called. Threads will not be in the cache if they are archived.
  If you need this information use on_raw_thread_delete() instead.
  Note that you can get the guild from Thread.guild.
  This requires Intents.guilds to be enabled.
  New in version 2.0.

  ## Parameters
  - thread - The thread that got deleted.
  '''

  on_raw_thread_update: Signal_[DRawThreadUpdateEvent] = pyqtSignal(object)
  '''
  Called whenever a thread is updated. Unlike on_thread_update() this is called regardless of the thread being in the internal thread cache or not.
  This requires Intents.guilds to be enabled.
  New in version 2.0.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_raw_thread_delete: Signal_[DRawThreadDeleteEvent] = pyqtSignal(object)
  '''
  Called whenever a thread is deleted. Unlike on_thread_delete() this is called regardless of the thread being in the internal thread cache or not.
  This requires Intents.guilds to be enabled.
  New in version 2.0.

  ## Parameters
  - payload - The raw event payload data.
  '''

  on_thread_member_join: Signal_[DThreadMember] = pyqtSignal(object)
  '''
  Called when a ThreadMember joins a Thread.
  You can get the thread a member belongs in by accessing ThreadMember.thread.
  This requires Intents.members to be enabled.
  New in version 2.0.

  ## Parameters
  - member - The member who joined or left.
  '''

  on_thread_member_remove: Signal_[DThreadMember] = pyqtSignal(object)
  '''
  Called when a ThreadMember leaves a Thread.
  You can get the thread a member belongs in by accessing ThreadMember.thread.
  This requires Intents.members to be enabled.
  New in version 2.0.

  ## Parameters
  - member - The member who joined or left.
  '''

  on_raw_thread_member_remove: Signal_[DRawThreadMembersUpdate] = pyqtSignal(object)
  '''
  Called when a ThreadMember leaves a Thread. Unlike on_thread_member_remove() this is called regardless of the member being in the internal thread's members cache or not.
  This requires Intents.members to be enabled.
  New in version 2.0.

  ## Parameters
  - payload - The raw event payload data.
  '''
  
################################ Voice ################################

  on_voice_state_update: Signal___[DMember, DVoiceState, DVoiceState] = pyqtSignal(object, object, object)
  '''
  Called when a Member changes their VoiceState.
  The following, but not limited to, examples illustrate when this event is called:
  - A member joins a voice or stage channel.
  - A member leaves a voice or stage channel.
  - A member is muted or deafened by their own accord.
  - A member is muted or deafened by a guild administrator.

  This requires Intents.voice_states to be enabled.

  ## Parameters
  - member - The member whose voice states changed.
  - before - The voice state prior to the changes.
  - after - The voice state after the changes.
  '''

class Client(DClient):

  def __init__(self) -> None:
    super().__init__(
      intents=DIntents.all(),
      status=DStatus.online,
      # status=DStatus.offline,
      activity=DGame('The Game'),
      # enable_debug_events=True
    )
    self.thread = Thread(
      target=self.run, args=(TOKEN,), #kwargs={'log_level' : DEBUG},
      name='Discord API Thread'
    )

  def submit(self, coro: Coroutine) -> Future:
    return submit(coro, self.loop)

  async def on_raw_app_command_permissions_update(self, *args):
    dsignals.on_raw_app_command_permissions_update.emit(*args)

  async def on_app_command_completion(self, *args):
    dsignals.on_app_command_completion.emit(*args)
  
  async def on_automod_rule_create(self, *args):
    dsignals.on_automod_rule_create.emit(*args)

  async def on_automod_rule_update(self, *args):
    dsignals.on_automod_rule_update.emit(*args)

  async def on_automod_rule_delete(self, *args):
    dsignals.on_automod_rule_delete.emit(*args)

  async def on_automod_action(self, *args):
    dsignals.on_automod_action.emit(*args)
  
  async def on_guild_channel_delete(self, *args):
    dsignals.on_guild_channel_delete.emit(*args)

  async def on_guild_channel_create(self, *args):
    dsignals.on_guild_channel_create.emit(*args)

  async def on_guild_channel_update(self, *args):
    dsignals.on_guild_channel_update.emit(*args)

  async def on_guild_channel_pins_update(self, *args):
    dsignals.on_guild_channel_pins_update.emit(*args)

  async def on_private_channel_update(self, *args):
    dsignals.on_private_channel_update.emit(*args)

  async def on_private_channel_pins_update(self, *args):
    dsignals.on_private_channel_pins_update.emit(*args)

  async def on_typing(self, *args):
    dsignals.on_typing.emit(*args)

  async def on_raw_typing(self, *args):
    dsignals.on_raw_typing.emit(*args)
  
  async def on_connect(self):
    dsignals.on_connect.emit()

  async def on_disconnect(self):
    dsignals.on_disconnect.emit()

  async def on_shard_connect(self, *args):
    dsignals.on_shard_connect.emit(*args)

  async def on_shard_disconnect(self, *args):
    dsignals.on_shard_disconnect.emit(*args)
  
  async def on_error(self, event: str, *args, **kwargs):
    dsignals.on_error.emit(ErrorSource(event, args, kwargs))

  async def on_socket_event_type(self, *args):
    dsignals.on_socket_event_type.emit(*args)

  async def on_socket_raw_receive(self, *args):
    dsignals.on_socket_raw_receive.emit(*args)

  async def on_socket_raw_send(self, *args):
    dsignals.on_socket_raw_send.emit(*args)
  
  async def on_ready(self):
    dsignals.on_ready.emit()

  async def on_resumed(self):
    dsignals.on_resumed.emit()

  async def on_shard_ready(self, *args):
    dsignals.on_shard_ready.emit(*args)

  async def on_shard_resumed(self, *args):
    dsignals.on_shard_resumed.emit(*args)
  
  async def on_guild_available(self, *args):
    dsignals.on_guild_available.emit(*args)

  async def on_guild_unavailable(self, *args):
    dsignals.on_guild_unavailable.emit(*args)

  async def on_guild_join(self, *args):
    dsignals.on_guild_join.emit(*args)

  async def on_guild_remove(self, *args):
    dsignals.on_guild_remove.emit(*args)

  async def on_guild_update(self, *args):
    dsignals.on_guild_update.emit(*args)

  async def on_guild_emojis_update(self, *args):
    dsignals.on_guild_emojis_update.emit(*args)

  async def on_guild_stickers_update(self, *args):
    dsignals.on_guild_stickers_update.emit(*args)

  async def on_audit_log_entry_create(self, *args):
    dsignals.on_audit_log_entry_create.emit(*args)

  async def on_invite_create(self, *args):
    dsignals.on_invite_create.emit(*args)

  async def on_invite_delete(self, *args):
    dsignals.on_invite_delete.emit(*args)

  async def on_integration_create(self, *args):
    dsignals.on_integration_create.emit(*args)

  async def on_integration_update(self, *args):
    dsignals.on_integration_update.emit(*args)

  async def on_guild_integrations_update(self, *args):
    dsignals.on_guild_integrations_update.emit(*args)

  async def on_webhooks_update(self, *args):
    dsignals.on_webhooks_update.emit(*args)

  async def on_raw_integration_delete(self, *args):
    dsignals.on_raw_integration_delete.emit(*args)

  async def on_interaction(self, *args):
    dsignals.on_interaction.emit(*args)

  async def on_member_join(self, *args):
    dsignals.on_member_join.emit(*args)

  async def on_member_remove(self, *args):
    dsignals.on_member_remove.emit(*args)

  async def on_raw_member_remove(self, *args):
    dsignals.on_raw_member_remove.emit(*args)

  async def on_member_update(self, *args):
    dsignals.on_member_update.emit(*args)

  async def on_user_update(self, *args):
    dsignals.on_user_update.emit(*args)

  async def on_member_ban(self, *args):
    dsignals.on_member_ban.emit(*args)

  async def on_member_unban(self, *args):
    dsignals.on_member_unban.emit(*args)

  async def on_presence_update(self, *args):
    dsignals.on_presence_update.emit(*args)

  async def on_message(self, *args):
    dsignals.on_message.emit(*args)

  async def on_message_edit(self, *args):
    dsignals.on_message_edit.emit(*args)

  async def on_message_delete(self, *args):
    dsignals.on_message_delete.emit(*args)

  async def on_bulk_message_delete(self, *args):
    dsignals.on_bulk_message_delete.emit(*args)

  async def on_raw_message_edit(self, *args):
    dsignals.on_raw_message_edit.emit(*args)

  async def on_raw_message_delete(self, *args):
    dsignals.on_raw_message_delete.emit(*args)

  async def on_raw_bulk_message_delete(self, *args):
    dsignals.on_raw_bulk_message_delete.emit(*args)
  
  async def on_reaction_add(self, *args):
    dsignals.on_reaction_add.emit(*args)

  async def on_reaction_remove(self, *args):
    dsignals.on_reaction_remove.emit(*args)

  async def on_reaction_clear(self, *args):
    dsignals.on_reaction_clear.emit(*args)

  async def on_reaction_clear_emoji(self, *args):
    dsignals.on_reaction_clear_emoji.emit(*args)

  async def on_raw_reaction_add(self, *args):
    dsignals.on_raw_reaction_add.emit(*args)

  async def on_raw_reaction_remove(self, *args):
    dsignals.on_raw_reaction_remove.emit(*args)

  async def on_raw_reaction_clear(self, *args):
    dsignals.on_raw_reaction_clear.emit(*args)

  async def on_raw_reaction_clear_emoji(self, *args):
    dsignals.on_raw_reaction_clear_emoji.emit(*args)
  
  async def on_guild_role_create(self, *args):
    dsignals.on_guild_role_create.emit(*args)

  async def on_guild_role_delete(self, *args):
    dsignals.on_guild_role_delete.emit(*args)

  async def on_guild_role_update(self, *args):
    dsignals.on_guild_role_update.emit(*args)

  async def on_scheduled_event_create(self, *args):
    dsignals.on_scheduled_event_create.emit(*args)

  async def on_scheduled_event_delete(self, *args):
    dsignals.on_scheduled_event_delete.emit(*args)

  async def on_scheduled_event_update(self, *args):
    dsignals.on_scheduled_event_update.emit(*args)

  async def on_scheduled_event_user_add(self, *args):
    dsignals.on_scheduled_event_user_add.emit(*args)

  async def on_scheduled_event_user_remove(self, *args):
    dsignals.on_scheduled_event_user_remove.emit(*args)

  async def on_stage_instance_create(self, *args):
    dsignals.on_stage_instance_create.emit(*args)

  async def on_stage_instance_delete(self, *args):
    dsignals.on_stage_instance_delete.emit(*args)

  async def on_stage_instance_update(self, *args):
    dsignals.on_stage_instance_update.emit(*args)
  
  async def on_thread_create(self, *args):
    dsignals.on_thread_create.emit(*args)

  async def on_thread_join(self, *args):
    dsignals.on_thread_join.emit(*args)

  async def on_thread_update(self, *args):
    dsignals.on_thread_update.emit(*args)

  async def on_thread_remove(self, *args):
    dsignals.on_thread_remove.emit(*args)

  async def on_thread_delete(self, *args):
    dsignals.on_thread_delete.emit(*args)

  async def on_raw_thread_update(self, *args):
    dsignals.on_raw_thread_update.emit(*args)

  async def on_raw_thread_delete(self, *args):
    dsignals.on_raw_thread_delete.emit(*args)

  async def on_thread_member_join(self, *args):
    dsignals.on_thread_member_join.emit(*args)

  async def on_thread_member_remove(self, *args):
    dsignals.on_thread_member_remove.emit(*args)

  async def on_raw_thread_member_remove(self, *args):
    dsignals.on_raw_thread_member_remove.emit(*args)
  
  async def on_voice_state_update(self, *args):
    dsignals.on_voice_state_update.emit(*args)

dsignals = DSignals()
client = Client()

__all__ = ['dsignals', 'client']
