from discord import TextChannel, VoiceChannel

from discord_app import discord

# TODO GET RID OF THIS

def has_unread_messages(channel: TextChannel | VoiceChannel) -> bool:
  expected = discord.state.last_message_id.get(channel.id, 0)
  return expected != channel.last_message_id

def get_icon_type(channel: TextChannel | VoiceChannel) -> tuple[str, str]:
  type = 'voice' if isinstance(channel, VoiceChannel) else 'text'
  if channel.is_nsfw():
    suffixes = ('-nsfw', ' (Age-Restricted)')
  elif not channel.permissions_for(channel.guild.default_role).view_channel:
    suffixes = ('-private', ' (Limited)')
  else:
    suffixes = ('', '')
  file_path = f'url("local:{type}-channel{suffixes[0]}.svg")'
  return file_path, type.capitalize() + suffixes[1]
