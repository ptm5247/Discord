from discord_app import discord

def main() -> None:
  discord.run()

if __name__ == '__main__':
  main()

# TODO time delay for some tooltips

# TODO DPI SCALING RAAAHHH

# TODO move components into components,
#      remove all class imports from discord_app if possible

# TODO
#   pure non-discord related extensions
#     ScrollArea, Settings, MultiShadow, ElidedXYZ, RoundedIconMixin?
#   QObjects whose appearance can be altered minorly by the Gateway
#     AssetBrush, Avatar(status), Username, Activity
