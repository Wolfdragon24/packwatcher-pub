#import
import discord
import requests
import os
import asyncio
import mcstatus

from discord.ext import commands, tasks
from pymongo import MongoClient
from mcstatus import MinecraftServer

#mcstatus info
#server object = server
#players: server.players.online / server.players.max / server.players.sample
#version: server.version.name / server.version.protocol
#description: server.description
#favicon: server.favicon

#socket.timeout -> query likely disabled

#db setup
cluster = MongoClient("")
db = cluster["discordbot"]
defaults = db["defaults"]

deservs = list(defaults.find())

def getindex(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None

class ServerStatus(commands.Cog):

    #status function
    @commands.command(aliases=['ss'])
    async def status(self, ctx, input="default"):

        if input == "default":

            if isinstance(ctx.channel, discord.channel.DMChannel):
                wmsg = 'You cannot use the .status command in DMs. Please run this command in a server or supply an IP request instead.'
                req = "If this error continues to occur and the current channel is not a DM, please ping or message Wolfdragon24#1477."
                warn = discord.Embed(title="Error - Default Server Status", color=0xeb1515)

                warn.add_field(name="Error", value=wmsg, inline=True)
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
            else:
                try:
                    await ctx.message.delete()
                except:
                    pass

                gid = ctx.message.guild.id

                defsrvindx = getindex(deservs,"guildid",gid)

                if defsrvindx != None:
                    a = deservs[defsrvindx]
                    sip = a["serverip"]

                    req = "Requested by " + ctx.message.author.name + "."

                    #fetch info from library
                    server = MinecraftServer.lookup(sip)
                    try:
                        info = server.status()

                        ip = sip
                        onoff = 'Server is currently online!'
                        po = info.players.online
                        pm = info.players.max

                        if po == 1:
                            pc = "There is currently: " + str(po) + "/" + str(pm) + " players online."
                        else:
                            pc = "There are currently: " + str(po) + "/" + str(pm) + " players online."

                        pl = None
                        if info.players.sample:
                            pl = discord.utils.escape_markdown(", ".join([player.name for player in info.players.sample]))

                        vraw = info.version.name
                        v = " ".join([string for string in vraw.split(" ") if not string.isalpha()])

                        #send message
                        embed = discord.Embed(title="Server Status", color=0x6edd67)

                        embed.add_field(name="Server IP", value=ip, inline=True)
                        embed.add_field(name="Online", value=onoff, inline=True)
                        embed.add_field(name="Player Count", value=pc, inline=True)
                        if pl:
                            embed.add_field(name="Players", value=pl, inline=True)
                        embed.add_field(name="Version", value=v, inline=True)
                        embed.set_footer(text=req)

                        await ctx.send(embed=embed)

                    except: #server offline
                        ip = sip
                        onoff = 'Server is currently offline!'

                        #send message
                        embed = discord.Embed(title="Server Status", color=0x6edd67)

                        embed.add_field(name="Server IP", value=ip, inline=True)
                        embed.add_field(name="Online", value=onoff, inline=True)
                        embed.set_footer(text=req)

                        await ctx.send(embed=embed)

                else:
                    warn = await ctx.send("A default server does not exist. Please set a default server with .setdefault (IP) and try again.")
                    await asyncio.sleep(5)
                    await warn.delete()
        else:
            #fetch info from api
            server = MinecraftServer.lookup(input)
            req = "Requested by " + ctx.message.author.name + "."

            try:
                await ctx.message.delete()
            except:
                pass

            try:
                info = server.status()

                ip = input
                onoff = 'Server is currently online!'
                po = info.players.online
                pm = info.players.max

                if po == 1:
                    pc = "There is currently: " + str(po) + "/" + str(pm) + " players online."
                else:
                    pc = "There are currently: " + str(po) + "/" + str(pm) + " players online."

                pl = None
                if info.players.sample:
                    pl = discord.utils.escape_markdown(", ".join([player.name for player in info.players.sample]))

                vraw = info.version.name
                v = " ".join([string for string in vraw.split(" ") if not string.isalpha()])

                #send message
                embed = discord.Embed(title="Server Status", color=0x6edd67)

                embed.add_field(name="Server IP", value=ip, inline=True)
                embed.add_field(name="Online", value=onoff, inline=True)
                embed.add_field(name="Player Count", value=pc, inline=True)
                if pl:
                    embed.add_field(name="Players", value=pl, inline=True)
                embed.add_field(name="Version", value=v, inline=True)
                embed.set_footer(text=req)

                await ctx.send(embed=embed)

            except: #server offline
                ip = input
                onoff = 'Server is currently offline!'

                #send message
                embed = discord.Embed(title="Server Status", color=0x6edd67)

                embed.add_field(name="Server IP", value=ip, inline=True)
                embed.add_field(name="Online", value=onoff, inline=True)
                embed.set_footer(text=req)

                await ctx.send(embed=embed)

    #set default function
    @commands.command()
    async def setdefault(self, ctx, serverip):

        if isinstance(ctx.channel, discord.channel.DMChannel):
            wmsg = 'You cannot use the .setdefault command in DMs. Please run this command in a server instead.'
            req = "If this error continues to occur and the current channel is not a DM, please ping or message Wolfdragon24#1477."
            warn = discord.Embed(title="Error - Set Default Server", color=0xeb1515)

            warn.add_field(name="Error", value=wmsg, inline=True)
            warn.set_footer(text=req)

            await ctx.send(embed=warn)

        else:
            await ctx.message.delete()

            if ctx.message.author.guild_permissions.manage_guild or ctx.author.id == 276976462140014593:
                try:
                    gid = ctx.message.guild.id
                    req = "Setting altered by " + ctx.message.author.name + "."

                    servindx = getindex(deservs,"guildid",gid)

                    if servindx != None:
                        defaults.update_one({"guildid":gid},{"$set":{"serverip":serverip}})
                        del deservs[servindx]
                        deservs.append({"guildid":gid,"serverip":serverip})
                    else:
                        defaults.insert_one({"guildid":gid,"serverip":serverip})
                        deservs.append({"guildid":gid,"serverip":serverip})

                    embed = discord.Embed(title="Default Server IP Updated!", color=0x6edd67)

                    embed.add_field(name="Server IP", value=serverip, inline=True)
                    embed.set_footer(text=req)

                    await ctx.send(embed=embed)
                except:
                    wmsg = 'Bot encountered an error while running the command: "setdefault" The default server IP could not be set.'
                    req = "If this error continues to occur, please ping or message Wolfdragon24#1477."
                    warn = discord.Embed(title="Error - Default Server IP", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
            else:
                wmsg = f'You do not have sufficient permissions to use this command.'
                warn = discord.Embed(title="Error - Insufficient Permissions", color=0xf5c242)

                warn.add_field(name="Error", value=wmsg, inline=True)

                req = "Requested by " + ctx.message.author.name + "."
                warn.set_footer(text=req)

                await ctx.send(embed=warn)

def setup(bot):
    bot.add_cog(ServerStatus(bot))
