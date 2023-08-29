import regex

from asyncio import run_coroutine_threadsafe as submit
from random import choice

from discord import Message, TextChannel, Object
from discord.app_commands import CommandTree
from discord.enums import ButtonStyle
from discord.interactions import Interaction
from discord.ui import View, Button, button
from discord.utils import MISSING

from . import root, signals, discord

target_guild = Object(982871992002813952) # MWTC
# target_guild = Object(771952039513161729) # frick

with open(root.absoluteFilePath('word-list.txt')) as file:
  word_list = set(word.strip() for word in file)

pattern = regex.compile(r'([-\w]+)')

def message(message: Message) -> None:
  if message.author.id != discord.api.user.id and \
    isinstance(message.channel, TextChannel) and \
    message.guild.id == target_guild.id:
    for match in pattern.finditer(message.content, overlapped=False):
      word = match.group(1)
      if word.upper() in word_list:
        coro = message.channel.send(f'{word}? I hardly know her!')
        submit(coro, discord.api.loop)
        break

signals.message.connect(message)
tree = CommandTree(discord.api)

class TicTacToe(View):

  class DifficultySelect(View):

    @button(label='Pog Mode', style=ButtonStyle.green)
    async def easy(self, interaction: Interaction, _) -> None:
      await interaction.response.edit_message(
        content='Click on a square to make a move.',
        view=TicTacToe(hard=False)
      )

    @button(label='Sicko Mode', style=ButtonStyle.red)
    async def hard(self, interaction: Interaction, _) -> None:
      await interaction.response.edit_message(
        content='Click on a square to make a move.',
        view=TicTacToe(hard=True)
      )

  class Button(Button):

    def __init__(self, parent: 'TicTacToe', row: int) -> None:
      super().__init__(emoji='◼️', row=row)
      self.parent = parent

    def set(self, emoji: str) -> None:
      self.style = ButtonStyle.blurple
      self.disabled = True
      self.emoji = emoji
    
    async def callback(self, interaction: Interaction) -> None:
      self.set('❌')
      await self.parent.take_turn(interaction)

  def __init__(self, hard=True) -> None:
    super().__init__(timeout=None)
    for r in range(3):
      for _ in range(3):
        self.add_item(self.Button(self, r))
    self.hard = hard
  
  WIN = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]

  async def take_turn(self, interaction: Interaction) -> None:
    board = [str(item.emoji) for item in self.children]
    if '◼️' not in board:
      await self.end_game(interaction, board)
    else:
      pos, _ = self.best_move(board, 1)
      board[pos] = '⭕'
      self.children[pos].set('⭕')
      if '◼️' not in board or self.score(board):
        await self.end_game(interaction, board)
      else:
        await interaction.response.edit_message(view=self)

  async def end_game(self, interaction: Interaction, board: list[str]) -> None:
    for item in self.children:
      item.disabled = True
    match self.score(board):
      case -1: content = 'You Win!'
      case 0:  content = "It's a draw..."
      case 1:  content = 'I Win!'
    await interaction.response.edit_message(content=content, view=self)

  @classmethod
  def score(cls, board: list[str]) -> int:
    for i, j, k in cls.WIN:
      if (mark := board[i]) != '◼️' and mark == board[j] == board[k]:
        return -1 if mark == '❌' else 1
    return 0
  
  def minmax(self, board: list[str], player: int) -> int:
    if x := self.score(board):
      return x * player
    pos, value = self.best_move(board, player)
    return value if pos != -1 else 0

  def best_move(self, board: list[str], player: int) -> tuple[int, int]:
    if self.hard:
      pos, value = -1, -2
      for i, mark in enumerate(board):
        if mark == '◼️':
          board[i] = '❌' if player == -1 else '⭕'
          score = -self.minmax(board, -player)
          if score > value:
            pos, value = i, score
          board[i] = '◼️'
      return pos, value
    else:
      possible = [i for i in range(len(board)) if board[i] == '◼️']
      return choice(possible), 0
   
@tree.command(guild=target_guild)
async def ttt(interaction: Interaction):
  '''Play Tic Tac Toe'''
  await interaction.response.send_message(
    content='Select a difficulty.',
    view=TicTacToe.DifficultySelect(timeout=None)
  )

# def api_ready() -> None:
#   submit(tree.sync(guild=target_guild), discord.api.loop)
# signals.api_ready.connect(api_ready)
