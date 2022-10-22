import discord
import requests
import mcstatus
from discord.ext.tasks import loop
import time
import datetime
import socket

from discord.ext import commands, tasks
from mcstatus import MinecraftServer

timestor = []
curday = ""

SERVER = 'play.wynncraft.com'

class PlayerCountLog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.LogWynnPlayers.start()

    @loop(minutes=1)
    async def LogWynnPlayers(self):
        global timestor
        global curday

        await self.bot.wait_until_ready()

        timenow = datetime.datetime.now()

        if str(timenow.hour) == 0 and curday != str(timenow.day):
            timestor = []
            curday = str(timenow.day)

        if str(timenow.hour) not in timestor:
            timestor.append(str(timenow.hour))

            server = MinecraftServer.lookup(SERVER)

            logchannel = self.bot.get_channel(960680426278637628)

            now = int(time.time())
            outputtime = f"<t:{now}>"

            embed = discord.Embed(title="Wynncraft - Player Tracker", color=0x6edd67)
            embed.add_field(name="Timestamp", value=outputtime)

            try:
                info = server.status()

                po = info.players.online
                pm = info.players.max

                pc = str(po) + "/" + str(pm) + " players."

                embed.add_field(name="Player Count", value=pc, inline=False)

            except socket.timeout:
                try:
                    info = requests.get(f'https://api.mcsrvstat.us/2/{SERVER}')

                    po = info["players"]["online"]
                    pm = info["players"]["max"]

                    pc = str(po) + "/" + str(pm) + " players."

                    embed.add_field(name="Player Count", value=pc, inline=False)
                except:
                    embed.add_field(name="Player Count", value="The Server could not be reached.", inline=False)

            except:
                embed.add_field(name="Player Count", value="The Server could not be reached.", inline=False)

            await logchannel.send(embed=embed)

def setup(bot):
    bot.add_cog(PlayerCountLog(bot))
