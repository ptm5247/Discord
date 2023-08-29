#   @state.for_current_guild_only
#   async def on_guild_channel_update(
#     self, before: GuildChannel, after: GuildChannel
#   ) -> None:
#     if before.name != after.name:
#       signals.guild_channel_name_update.emit(after)
#     if not isinstance(after, CategoryChannel) and \
#       utils.get_icon_type(before) != utils.get_icon_type(after):
#       signals.guild_channel_icon_update.emit(after)
#     if before.category != after.category or \
#       before.position != after.position:
#       signals.guild_channel_position_update.emit(after)
#     if hasattr(after, 'topic') and before.topic != after.topic:
#       signals.guild_channel_topic_update.emit(after)

#   async def on_ready(self) -> None:
#     signals.api_ready.emit()

#   async def on_guild_join(self, guild: Guild) -> None:
#     signals.guild_join.emit(guild)

#   async def on_guild_remove(self, guild: Guild) -> None:
#     signals.guild_remove.emit(guild)
  
#   async def on_guild_update(self, before: Guild, after: Guild) -> None:
#     if before.name != after.name:
#       signals.guild_name_update.emit(after)
#     if before.icon != after.icon:
#       signals.guild_icon_update.emit(before, after)

#   @state.for_current_channel_only
#   async def on_member_join(self, member: Member) -> None:
#     signals.member_join.emit(member)

#   @state.for_current_channel_only
#   async def on_member_remove(self, member: Member) -> None:
#     signals.member_remove.emit(member)

#   @state.for_current_channel_only
#   async def on_member_update(self, before: Member, after: Member) -> None:
#     if before.roles != after.roles:
#       signals.member_roles_update.emit(after)
#     if before.display_name != after.display_name:
#       signals.member_name_update.emit(after)
#     if before.display_avatar != after.display_avatar:
#       signals.member_avatar_update.emit(before, after)
#     if before.color != after.color:
#       signals.member_color_update.emit(after)

#   @state.for_current_channel_only
#   async def on_presence_update(self, before: Member, after: Member) -> None:
#     if before.activity != after.activity:
#       signals.member_activity_update.emit(after)
#     if before.raw_status != after.raw_status:
#       signals.member_status_update.emit(after)
#       if before.raw_status == 'offline' or after.raw_status == 'offline':
#         signals.member_online_update.emit(after)
  
#   async def on_message(self, message: Message) -> None:
#     signals.message.emit(message)

#   async def on_raw_reaction_add(self, payload: RawReactionActionEvent) -> None:
#     signals.raw_reaction_action.emit(payload)

#   async def on_raw_reaction_remove(
#     self, payload: RawReactionActionEvent
#   ) -> None:
#     signals.raw_reaction_action.emit(payload)

#   @state.for_current_guild_only
#   async def on_guild_role_create(self, role: Role) -> None:
#     signals.guild_role_create.emit(role)

#   @state.for_current_guild_only
#   async def on_guild_role_delete(self, role: Role) -> None:
#     signals.guild_role_delete.emit(role)

#   @state.for_current_guild_only
#   async def on_guild_role_update(self, before: Role, after: Role) -> None:
#     if before.hoist != after.hoist:
#       signals.guild_role_hoist_update.emit(after)
#     if before.position != after.position:
#       signals.guild_role_position_update.emit(after)
#     if before.color != after.color:
#       for member in after.members:
#         signals.member_color_update.emit(member)
#     if before.name != after.name and after.hoist:
#       signals.guild_role_name_update.emit(after)
  