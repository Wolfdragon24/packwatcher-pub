#import
import discord
import requests
import os
import asyncio

from discord.ext import commands

class UserSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #user search function
    @commands.command()
    async def user(self, ctx, search):

        req = "Requested by " + ctx.message.author.name + "."

        try:
            user = requests.get('https://playerdb.co/api/player/minecraft/' + search)
            user_json = user.json()
            pastname = ""
            playerdata = user_json["data"]["player"]
            names = playerdata["meta"]["name_history"]

            for i in names:
                a = i['name']
                if pastname == "":
                    pastname = str(pastname) + str(a)
                else:
                    pastname = str(pastname) + ", " + str(a)

            uname = playerdata["username"]
            uuid = playerdata["raw_id"]
            formuuid = playerdata["id"]
            avatar = playerdata["avatar"]            

            pastname = discord.utils.escape_markdown(pastname)
            uname = discord.utils.escape_markdown(uname)

            embed = discord.Embed(title="User Info - Minecraft", color=0x6edd67)

            embed.set_image(url=avatar)
            embed.add_field(name="Username", value=uname, inline=True)
            embed.add_field(name="UUID", value=uuid, inline=True)
            embed.add_field(name="Formatted UUID", value=formuuid, inline=True)
            embed.add_field(name="Past Usernames", value=pastname, inline=True)
            embed.set_footer(text=req)

            await ctx.send(embed=embed)
            await ctx.message.delete()
        except:
            search = discord.utils.escape_markdown(search)
            embed = discord.Embed(title="Error - Player Not Found", color=0xff0000)

            embed.add_field(name="Username/UUID", value=search, inline=True)
            embed.add_field(name="Error", value="No player with this username or UUID was found.", inline=True)
            embed.set_footer(text=req)

            await ctx.send(embed=embed)
            await ctx.message.delete()

def setup(bot):
    bot.add_cog(UserSearch(bot))
