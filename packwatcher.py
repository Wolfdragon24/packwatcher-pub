#import
import discord
import requests
import os
import asyncio
import traceback
import tracemalloc

from discord.ext import commands, tasks
from discord.ext.commands import CommandNotFound

tracemalloc.start()

intents = discord.Intents.all()


bot = commands.Bot(command_prefix='.',intents=intents)
bot.remove_command("help")

#-------------------------------------------------------------------------
lxahiddencommands = [642334236573040681, 877157413168484432]
roles = [700551758753300531,665010122107650078,852755422183817236]

#-------------------------------------------------------------------------

@bot.command()
async def help(ctx, override=None):
    global roles
    global lxahiddencommands

    req = "Requested by " + ctx.message.author.name + "."

    embed = discord.Embed(title="Commands", color=0xf5a742)

    embed.add_field(name=".status <IP/Hostname>(Optional)", value="Gives information about the default/preset server or an inputted server (Alias: .ss)", inline=True)
    embed.add_field(name=".setdefault <IP/Hostname>", value="Set the default server IP [Manage Server Permissions]", inline=True)
    embed.add_field(name=".user <Username>", value="Displays UUID and past usernames", inline=True)
    embed.add_field(name=".hypixelcheck <Username>",value="Displays Hypixel online status for a user (Alias: .hypixelstatus)",inline=True)
    embed.add_field(name=".bedwarsinfo <Username>",value="Displays Bedwars statistics for a user (Alias: .bedwarsstats)",inline=True)

    if ctx.author.id == 276976462140014593:
        if override == "hard": #ignore all restrictions
            embed.add_field(name=".lxa", value="Displays all territories and FFAs owned by LXA - Wynncraft", inline=True)
            embed.add_field(name=".activity <Guild Name/Prefix>", value="Displays the days since members' last joins - Wynncraft", inline=True)
            embed.add_field(name=".playtime <arguments/help>", value="Displays total playtime of all members in specific guilds - Wynncraft\n*If trying to enter a multi-word guild name, please enclose it in quotation marks or use the prefix.*", inline=True)
            embed.add_field(name=".members <guild>", value="Displays all members in a guild - Wynncraft", inline=True)
            embed.add_field(name=".pings <enable/disable> <channel>(Optional)", value="Toggles whether the bot pings roles in the current or inputted channel (Alias: .ping) - Wynncraft [Manage Server Permissions]", inline=True)
            embed.add_field(name=".ally", value="Lists ally list for territory tracking. - Wynncraft [Specific Roles]",inline=True)
            embed.add_field(name=".ally check <guild>", value="Checks if inputted guild is in ally list. - Wynncraft [Specific Roles]",inline=True)
            embed.add_field(name=".ally <add/remove> <guild>", value="Adds or removes inputted guild from ally list dependent on arguments. - Wynncraft [Specific Roles]",inline=True)
            embed.add_field(name=".setnewters <Territories>",value="Sets territories, '|' used as divider between sections, '-' used as divider between category and territory. - Wynncraft [Bot Owner]")
            embed.add_field(name=".tersupdate",value="Updates territories from database - Wynncraft [Bot Owner]")
            embed.add_field(name=".setcritters",value="Sets critical territories, '|' used as divider between HQ/Crits, ',' used as divider between territories. - Wynncraft [Bot Owner]")
            embed.add_field(name=".crittersupdate",value="Updates territories from database - Wynncraft [Bot Owner]")
            embed.add_field(name=".wynndebug",value="Displays debug information - Wynncraft [Bot Owner]")
            embed.add_field(name=".fallback <Type(territory/sessions)(Optional)> <Change>(Optional)",value="Activates fallback mode for LXA territory checking - Wynncraft [Bot Owner]")
            embed.add_field(name=".exclusive <add/remove/list>",value="Alters Exclusive users for ratelimiting - Wynncraft [Bot Owner]")
        elif override == "soft": #obey all restrictions, ignore bot owner perms
            if ctx.guild.id not in lxahiddencommands:
                embed.add_field(name=".lxa", value="Displays all territories and FFAs owned by LXA - Wynncraft", inline=True)
                embed.add_field(name=".activity <Guild Name/Prefix>", value="Displays the days since members' last joins - Wynncraft", inline=True)
                embed.add_field(name=".playtime <arguments/help>", value="Displays total playtime of all members in specific guilds - Wynncraft\n*If trying to enter a multi-word guild name, please enclose it in quotation marks or use the prefix.*", inline=True)
                embed.add_field(name=".members <guild>", value="Displays all members in a guild - Wynncraft", inline=True)
                embed.add_field(name=".pings <enable/disable> <channel>(Optional)", value="Toggles whether the bot pings roles in the current or inputted channel (Alias: .ping) - Wynncraft [Manage Server Permissions]", inline=True)

                if (ctx.guild.id in [664581414817234995,606830291838959626] and any(role for role in roles if role in [mrole.id for mrole in ctx.message.author.roles])):
                    embed.add_field(name=".ally", value="Lists ally list for territory tracking. - Wynncraft [Specific Roles]",inline=True)
                    embed.add_field(name=".ally check <guild>", value="Checks if inputted guild is in ally list. - Wynncraft [Specific Roles]",inline=True)
                    embed.add_field(name=".ally <add/remove> <guild>", value="Adds or removes inputted guild from ally list dependent on arguments. - Wynncraft [Specific Roles]",inline=True)
        else: #obey all restrictions, include bot owner perms
            if ctx.guild.id not in lxahiddencommands:
                embed.add_field(name=".lxa", value="Displays all territories and FFAs owned by LXA - Wynncraft", inline=True)
                embed.add_field(name=".activity <Guild Name/Prefix>", value="Displays the days since members' last joins - Wynncraft", inline=True)
                embed.add_field(name=".playtime <arguments/help>", value="Displays total playtime of all members in specific guilds - Wynncraft\n*If trying to enter a multi-word guild name, please enclose it in quotation marks or use the prefix.*", inline=True)
                embed.add_field(name=".members <guild>", value="Displays all members in a guild - Wynncraft", inline=True)
                embed.add_field(name=".pings <enable/disable> <channel>(Optional)", value="Toggles whether the bot pings roles in the current or inputted channel (Alias: .ping) - Wynncraft [Manage Server Permissions]", inline=True)

                if (ctx.guild.id in [664581414817234995,606830291838959626] and any(role for role in roles if role in [mrole.id for mrole in ctx.message.author.roles])):
                    embed.add_field(name=".ally", value="Lists ally list for territory tracking. - Wynncraft [Specific Roles]",inline=True)
                    embed.add_field(name=".ally check <guild>", value="Checks if inputted guild is in ally list. - Wynncraft [Specific Roles]",inline=True)
                    embed.add_field(name=".ally <add/remove> <guild>", value="Adds or removes inputted guild from ally list dependent on arguments. - Wynncraft [Specific Roles]",inline=True)

                embed.add_field(name=".setnewters <Territories>",value="Sets territories, '|' used as divider between sections, '-' used as divider between category and territory. - Wynncraft [Bot Owner]")
                embed.add_field(name=".tersupdate",value="Updates territories from database - Wynncraft [Bot Owner]")
                embed.add_field(name=".setcritters",value="Sets critical territories, '|' used as divider between HQ/Crits, ',' used as divider between territories. - Wynncraft [Bot Owner]")
                embed.add_field(name=".crittersupdate",value="Updates territories from database - Wynncraft [Bot Owner]")
                embed.add_field(name=".wynndebug",value="Displays debug information - Wynncraft [Bot Owner]")
                embed.add_field(name=".fallback <Type(territory/sessions)(Optional)> <Change>(Optional)",value="Activates fallback mode for LXA territory checking - Wynncraft [Bot Owner]")
                embed.add_field(name=".exclusive <add/remove/list>",value="Alters Exclusive users for ratelimiting - Wynncraft [Bot Owner]")
    else:
        if ctx.guild.id not in lxahiddencommands:
            embed.add_field(name=".lxa", value="Displays all territories and FFAs owned by LXA - Wynncraft", inline=True)
            embed.add_field(name=".activity <Guild Name/Prefix>", value="Displays the days since members' last joins - Wynncraft", inline=True)
            embed.add_field(name=".playtime <arguments/help>", value="Displays total playtime of all members in specific guilds - Wynncraft\n*If trying to enter a multi-word guild name, please enclose it in quotation marks or use the prefix.*", inline=True)
            embed.add_field(name=".members <guild>", value="Displays all members in a guild - Wynncraft", inline=True)
            embed.add_field(name=".pings <enable/disable> <channel>(Optional)", value="Toggles whether the bot pings roles in the current or inputted channel (Alias: .ping) - Wynncraft [Manage Server Permissions]", inline=True)

            if (ctx.guild.id in [664581414817234995,606830291838959626] and any(role for role in roles if role in [mrole.id for mrole in ctx.message.author.roles])):
                embed.add_field(name=".ally", value="Lists ally list for territory tracking. - Wynncraft [Specific Roles]",inline=True)
                embed.add_field(name=".ally check <guild>", value="Checks if inputted guild is in ally list. - Wynncraft [Specific Roles]",inline=True)
                embed.add_field(name=".ally <add/remove> <guild>", value="Adds or removes inputted guild from ally list dependent on arguments. - Wynncraft [Specific Roles]",inline=True)
            if ctx.author.id == 276976462140014593:
                embed.add_field(name=".setnewters <Territories>",value="Sets territories, '|' used as divider between sections, '-' used as divider between category and territory. - Wynncraft [Bot Owner]")
                embed.add_field(name=".tersupdate",value="Updates territories from database - Wynncraft [Bot Owner]")
                embed.add_field(name=".setcritters",value="Sets critical territories, '|' used as divider between HQ/Crits, ',' used as divider between territories. - Wynncraft [Bot Owner]")
                embed.add_field(name=".crittersupdate",value="Updates territories from database - Wynncraft [Bot Owner]")
                embed.add_field(name=".wynndebug",value="Displays debug information - Wynncraft [Bot Owner]")
                embed.add_field(name=".fallback <Type(territory/sessions)(Optional)> <Change>(Optional)",value="Activates fallback mode for LXA territory checking - Wynncraft [Bot Owner]")
                embed.add_field(name=".exclusive <add/remove/list>",value="Alters Exclusive users for ratelimiting - Wynncraft [Bot Owner]")

    embed.add_field(name=".help <Override(hard/soft)>", value="Displays this menu", inline=True)
    embed.add_field(name=".invite", value="Shows invite link", inline = True)
    embed.set_footer(text=req)

    await ctx.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def sechelp(ctx, keep=None):

    if ctx.message.author.id == 276976462140014593:
        embed = discord.Embed(title="Hidden Commands", color=0xf5a742)

        embed.add_field(name=".delrole <rolename/role ping>", value="Hidden Command", inline= True)
        embed.add_field(name=".eval <statement>", value="Hidden Command", inline= True)
        embed.add_field(name=".asynceval <statement>", value="Hidden Command", inline=True)
        embed.add_field(name=".exec <code>", value="Hidden Command", inline=True)
        embed.add_field(name=".copy <statement>", value="Hidden Command", inline= True)
        embed.add_field(name=".embedcopy <statement>", value="Hidden Command", inline= True)
        embed.add_field(name=".listsrvs", value="Hidden Command", inline=True)
        embed.add_field(name=".listcnls <server id>",value="Hidden Command", inline=True)
        embed.add_field(name=".addsrv",value="Hidden Command - EspChar correction", inline=True)

        if not keep:
            embed.set_footer(text="This message will self-destruct in 3 seconds!!")

        sechelpmsg = await ctx.send(embed=embed)
        await ctx.message.delete()

        if not keep:
            await asyncio.sleep(3)
            await sechelpmsg.delete()

@bot.command()
async def invite(ctx):

    req = "Requested by " + ctx.message.author.name + "."

    embed = discord.Embed(title="Invite", color=0xa9e88b)

    embed.add_field(name="Bot Invite", value="You can invite me to any server by clicking [here](https://discord.com/api/oauth2/authorize?client_id=606829493193277441&permissions=8&scope=bot)", inline=True)
    embed.set_footer(text=req)

    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send(embed=embed)

@bot.command()
async def logmemd(ctx):
    if ctx.message.author.id == 276976462140014593:
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')

        out = "[ Top 10 ]"
        for stat in top_stats[:10]:
            out += f"\n{stat}"

        await ctx.send(out)

@bot.command()
async def logmemc(ctx):
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("[ Top 10 ]")
    for stat in top_stats[:10]:
        print(stat)
        
@bot.event
async def on_command_error(ctx, error):
    ignores = {
            121,    # the semaphore timeout period has expired
        }
    if (isinstance(error, CommandNotFound)) or (isinstance(error, OSError) and error in ignores):
        return
    else:
        raise error
        errorchannel = self.bot.get_channel(837917735089340446)
        embed = discord.Embed(title="Generic PackWatcher Error", color=0xeb1515)

        embed.add_field(name="Error",value=f"An error occurred in typical operation.")

        req = "Automated Error Logging."
        embed.set_footer(text=req)

        error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
        ertext = f"```{error}```"

        await errorchannel.send(embed=embed)
        await errorchannel.send(ertext)

#-------------------------------------------------------------------------

#current cogs: "cogs.serverstatus","cogs.usersearch","cogs.secret","cogs.wynnmodule","cogs.hypixelmodule","cogs.niatracker","cogs.playercountlog","cogs.lxasheetmanager"

#load cogs
extensions = ["cogs.serverstatus","cogs.usersearch","cogs.secret","cogs.wynnmodule","cogs.hypixelmodule","cogs.niatracker","cogs.lxasheetmanager"]

for i in extensions:
    bot.load_extension(i)

#discord bot
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))

#-------------------------------------------------------------------------

bot.run(token)
