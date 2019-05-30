import os, datetime
import asyncio
import pprint

import discord
from discord.ext import commands

from exceptions import *


class khaaliStats(commands.Cog):
  def __init__(self, bot, db_name='khaaliDiscord', logname='khaaliStats'):
    self.bot = bot
    self.db = self.Database(db_name)
    self.logger = self.Logs(logname)
    self.talk = self.Messages()
    self.cmds = self.Commands(bot)

  @commands.Cog.listener()
  async def on_ready(self):
    print('Mmm lets track some spicy stats')

  @commands.Cog.listener()
  async def on_resumed(self):
    pass

  @commands.Cog.listener()
  async def on_message(self, msg):
    pass

  @commands.Cog.listener()
  async def on_error(self, event, *args):
    pass

  @commands.Cog.listener()
  async def on_guild_join(self, guild):
    def is_guild_owner_dm(m): return m.author == guild.owner and type(m) == discord.DMChannel
    YES = ('y','yes','yup','yep'); NO = ('n','no','nup','nope') # TODO: Module for consts?
    dm = guild.owner.dm_channel if guild.owner.dm_channel else guild.owner.create_dm()
    if not self.db.exists_in_db(guild.id, 'Guild'):
      new_guild = True
      await dm.send(content=self.talk.first_join(guild.owner), embed=self.talk.channel_id_embed())
    else:
      new_guild = False
      await dm.send(content=self.talk.rejoin(guild.owner))
      stats = guild.get_channel(self.db.get_stats_channel_id(guild.id))
      await dm.send('Is {0.mention} still the stats channel?'.format(stats))
    while True:
      try: await msg = self.bot.wait_for('message', check=is_guild_owner_dm, timeout=30.0)
      except asyncio.TimeoutError: await dm.send('Timed out. Bruh I can\'t do stats if I can\'t speak')
      else:
        txt = msg.content.strip().lower() 
        if txt in YES: 
          break
        elif txt in NO: 
          await dm.send('Please send the new stats channel ID', embed=self.talk.channel_id_embed())
        else:
          channel = guild.get_channel(txt)
          if channel:
            if self.db.update_stats_channel(guild.id, channel.id):
              await dm.send('Stats channel updated to {0.mention}'.format(channel))
            stats = channel
            break
          else: await dm.send('Some error occurred. Please try again.')
    self.setup_guild(guild) # TODO Here
    if new_guild:
      data = {
        name: guild.name,
        discord_id: guild.id,
        owner_id: guild.owner_id,
        stats_chan_id: stats.id,
        created_at: guild.created_at
      }
      self.db.insert('Guild', data)
    self.db.update_guild_data('Member', guild.id, guild.members)
    self.db.update_guild_data('Role', guild.id, guild.roles)
    self.db.update_guild_data('Channel', guild.id, guild.channels)
    self.db.update_guild_data('Webhook', guild.id, guild.webhooks) # Requires `manage_webhooks`
    await stats.send('Here are some spicy stats',embed=self.talk.get_stats_by_guild(guild.id, self.db))

  @commands.Cog.listener()
  async def on_guild_remove(self, guild):
    pass


  ''' Message ops '''

  @commands.Cog.listener()
  async def on_raw_message_delete(self, payload):
    pass

  @commands.Cog.listener()
  async def on_raw_message_edit(self, payload):
    pass

  @commands.Cog.listener()
  async def on_raw_bulk_message_delete(self, payload):
    pass

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    pass

  @commands.Cog.listener()
  async def on_raw_reaction_remove(self, payload):
    pass

  @commands.Cog.listener()
  async def on_raw_reaction_clear(self, rx):
    pass

  @commands.Cog.listener()
  async def on_private_channel_pins_update(self, channel, last):
    pass

  @commands.Cog.listener()
  async def on_guild_channel_pins_update(self, channel, last):
    pass


  ''' Member ops '''

  @commands.Cog.listener()
  async def on_member_join(self, mem):
    pass

  @commands.Cog.listener()
  async def on_member_remove(self, mem):
    pass

  @commands.Cog.listener()
  async def on_member_ban(self, guild, mem):
    pass

  @commands.Cog.listener()
  async def on_member_unban(self, guild, mem):
    pass


  ''' Role ops '''

  @commands.Cog.listener()
  async def on_guild_role_create(self, role):
    pass

  @commands.Cog.listener()
  async def on_guild_role_delete(self, role):
    pass  

  @commands.Cog.listener()
  async def on_guild_role_update(self, before, after):
    pass


  ''' Channel ops '''

  @commands.Cog.listener()
  async def on_guild_channel_create(self, channel):
    pass
    
  @commands.Cog.listener()
  async def on_guild_channel_delete(self, channel):
    pass

  @commands.Cog.listener()
  async def on_guild_channel_update(self, before, after):
    pass


  ''' Guild updates '''

  @commands.Cog.listener()
  async def on_guild_update(self, before, after):
    pass

  @commands.Cog.listener()
  async def on_webhooks_update(self, channel):
    pass

  # @commands.Cog.listener()
  # async def on_guild_integrations_update(self, guild):
  #   pass



  # Update from DM instead?
  @commands.command()
  async def update(self, ctx, *args):
    pass


  class Database():
    ''' Schema for `khaaliDiscord`
    [Collection] members: {
      name: str,
      handle: str,
      nick: str,
      created: date,
      joined_first: date,
      left: date,
      rejoined: date,
      roles: [],
      bot: boolean
    }
    [Collection] channels: {
      name: str,
      id: int,
      created: date,
      guild_id: int,
      private: boolean,
      voice: boolean
    }
    [Collection] roles: {
      name: str,
      purpose: str,
      value: int,
      perms: [],
      created: date
    }
    [Collection] webhooks: {

    }
    [Collection] integrations: {

    }
    [Collection] guilds: {
      name: str,
      discord_id: int,
      owner_id: int,
      stats_chan_id: int,
      members: [],
      channels: [],
      roles: [],
      webhooks: [],
      integrations: []
    }'''
    def __init__(self, db_name):
      self.connection = None
      try: from pymongo import MongoClient
      except ImportError: print('No pyMongo!')
      else: self.connection = MongoClient()[db_name]
      self.collections = {
        'Member': self.connection.members,
        'Channel': self.connection.channels,
        'Role': self.connection.roles,
        'Webhook': self.connection.webhooks,
        'Integration': self.connection.webhooks,
        'Guild': self.connection.guilds
      }

    # coll: Member | Channel | Role | Webhook | Integration | Guild
    def exists_in_db(self, id, coll):
      res = None
      if coll in self.collections.keys(): res = self.collections[coll].find({'discord_id': id})
      else: raise InvalidCollection(coll)
      return True if res else False

    def get_stats_channel_id(self, guild_id):
      res = self.collections['Guild'].find({'discord_id': guild_id})
      # Check if ID exists
      return res.stats_chan_id

    def update_stats_channel_id(self, guild_id, channel_id): 
      self.collections['Guild'].find_one_and_update(
        {'discord_id': guild_id}, 
        {'stats_chan_id': channel_id}
      )
    
    def update_guild_data(coll, guild_id, data):
      if not coll in self.collections.keys(): raise InvalidCollection(coll)
      for elem in data:
        if not self.exists_in_db(elem.id,coll):
          pass # Insert new doc
        else:
          pass # Update doc if required
    
    def insert(self, coll, doc):
      # Check if already exists
      if coll in self.collections.keys(): self.collections[coll].insert(doc)
      else: raise InvalidCollection(coll)

  class Messages():
    def __init__(self):
      pass
    
    def welcome_message(self, first):
      if first: return 'You made a wise choice! Let\'s do some stats!'
      else: return 'Thanks for adding me back fam!'

    def channel_id_embed(self):
      em = discord.Embed()
      # em.set_image(url='https://khaalidimaag.io/discord/khaaliStats/channel_id.gif')
      em.set_footer(text=':point_up_2: Send the channel ID fam')  
      em.set_author(name='khaaliStats',url='https://khaalidimaag.io/discord/khaaliStats')
      return em

    def first_join(self, owner):
      pass

    def rejoin(self, owner):
      pass
    
    ''' category default: (all) = int(1111,10) = 15
      b3.b2.b1.b0 = webhooks.roles.channels.members
    '''
    def get_stats_by_guild(self, guild_id, db, category=15):
      pass

  class Logs():
    def __init__(self, logname):
      import logging
      pass

  class Commands():
    def __init__(self, bot):
      pass

    @commands.command()
    async def members(self, ctx, *args):
      pass

    @commands.command()
    async def channels(self, ctx, *args):
      pass

    @commands.command()
    async def roles(self, ctx, *args):
      pass

    @commands.command()
    async def projects(self, ctx, *args):
      pass

    @commands.command()
    async def all(self, ctx, *args):
      pass
  


  def setup_guild(self, guild):
    query = self.db.guilds.find({'id':guild.id})
    current = {
      'name': guild.name,
      'id': guild.id,
      'owner_id': guild.owner_id
    }
    if query:
      if guild.get_channel(query.stats_chan_id): current.stats_chan_id = query.stats_chan_id
      else: current.stats_chan_id = self.get_stats_chan(guild,first=False)
      if current != query: self.db.guilds.update_one(query,current)
    else:
      current.stats_chan_id = self.get_stats_chan(guild)
      self.db.guilds.insert_one(current)
    self.update_guild_in_db(guild)
    self.send_stats(guild.get_channel(current.stats_chan_id))
    
  def update_guild_in_db(self,guild):
    for member in guild.members:
      # Add to db
      pass
    for role in guild.roles:
      # Add to db
      pass
    for channel in guild.channels:
      # Add to db
      pass
    pass

  async def get_stats_chan(self, guild, first=True):
    owner = guild.get_member(guild.owner_id)
    dm = await owner.create_dm() if not owner.dm_channel else owner.dm_channel
    def check(m): return m.channel.id == dm.id and m.author == owner_id
    await dm.send(content=self.welcome_message(first), embed=self.channel_id_embed())
    while True:
      try: msg = await self.bot.wait_for('message', check=check, timeout=60.0)
      except asyncio.TimeoutError: await dm.send('Dont leave me hanging buddy!')
      else: 
        stats = guild.get_channel(msg.content)
        if not stats: 
          await dm.send('Channel not found in {0.name}. Please send the ID again.'.format(guild))
          continue
        if type(stats) != discord.TextChannel:
          await dm.send('Channel is not a Text Channel. How am I supposed to send stats?')
          continue
        await dm.send('Head on over to {0.mention} for the current stats of {1.name}'.format(stats,guild))
        return stats.id


  def welcome_message(self, first):
    if first: return 'You made a wise choice! Let\'s do some stats!'
    else: return 'Thanks for adding me back fam!'

  def channel_id_embed(self):
    em = discord.Embed()
    # em.set_image(url='https://khaalidimaag.io/discord/khaaliStats/channel_id.gif') # NOTE: Link not active
    em.set_footer(text=':point_up_2: Send the channel ID fam')  
    em.set_author(name='khaaliStats',url='https://khaalidimaag.io/discord/khaaliStats')
    return em


  ''' category default: (all) = int(1111,10) = 15
    b3.b2.b1.b0 = webhooks.roles.channels.members
  '''
  async def send_stats(channel, category=15):
    em = discord.Embed(
      title='Current stats of {0.name}'.format(channel.guild),
      timestamp=datetime.datetime.now(),
      color=0xFFFFFF
    )
    # TODO Add data lol
    em.set_author(name='khaaliStats',url='https://khaalidimaag.io/discord/khaaliStats')
    await channel.send(embed=em)


def setup(bot): bot.add_cog(khaaliStats(bot))

if __name__=='__main__':
  bot = commands.Bot(command_prefix='~')
  setup(bot)