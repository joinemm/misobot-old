from discord.ext import commands
import main
import asyncio
from utils import logger as misolog
from utils import misc as misomisc

database = main.database


class Mod:

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, mention=None, time=None):
        """Mute the given user"""
        self.logger.info(misolog.format_log(ctx, f""))
        role_id = database.get_attr("guilds", f"{ctx.guild.id}.muterole", 0)
        muterole = ctx.message.guild.get_role(role_id)
        if muterole is None:
            await ctx.send(f"Muterole for this server is invalid or not set, please use >config muterole")
            return
        if mention is None:
            await ctx.send(f"Give me someone to mute!")
            return
        if time is not None:
            try:
                time = int(time)
            except ValueError:
                await ctx.send(f"Invalid timeframe `{time}`. Please give time in minutes")
                return
        member = misomisc.user_from_mention(ctx.guild, mention)
        if member is None:
            await ctx.send("ERROR: Invalid user")
            return
        if member.id == 133311691852218378:
            await ctx.send(f"Sorry but I will not mute this person!")
            return

        await member.add_roles(muterole)
        await ctx.send(f"Muted {member.mention}" + (f" for {time} minutes" if time is not None else ""))

        if time is not None:
            await asyncio.sleep(time * 60)
            if muterole in member.roles:
                await member.remove_roles(muterole)
                await ctx.send(f"Unmuted {member.mention} ({time} minutes passed)")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, mention=None):
        """Unmute the given user"""
        self.logger.info(misolog.format_log(ctx, f""))
        role_id = database.get_attr("guilds", f"{ctx.guild.id}.muterole", 0)
        muterole = ctx.message.guild.get_role(role_id)
        if muterole is None:
            await ctx.send(f"Muterole for this server is invalid or not set, please use >config muterole")
            return
        if mention is None:
            await ctx.send(f"Give me someone to unmute!")
            return

        member = misomisc.user_from_mention(ctx.guild, mention)
        if member is None:
            await ctx.send("ERROR: Invalid user")
            return

        await member.remove_roles(muterole)
        await ctx.send(f"Unmuted {member.mention}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, mode=None, arg=None):
        """Set bot parameters like welcome channel and mute role"""
        self.logger.info(misolog.format_log(ctx, f""))

        if mode in ["welcome", "welcomechannel"]:
            if arg is not None:
                channel = misomisc.channel_from_mention(ctx.guild, arg)
                if channel is not None:
                    database.set_attr("guilds", f"{ctx.guild.id}.welcome_channel", channel.id)
                    await ctx.send(f"Welcome channel for {ctx.guild.name} set to {channel.mention}")
                else:
                    await ctx.send("ERROR: Invalid channel")
            else:
                await ctx.send(f"ERROR: Please give a channel to set the as the welcome channel")

        elif mode in ["mute", "muterole"]:
            role = misomisc.role_from_mention(ctx.guild, arg)
            if role is not None:
                database.set_attr("guilds", f"{ctx.guild.id}.muterole", role.id)
                await ctx.send(f"Mute role for {ctx.guild.name} set to `@{role.name} ({role.id})`")
            else:
                await ctx.send("ERROR: Invalid role")

        elif mode == "autorole":
            role = misomisc.role_from_mention(ctx.guild, arg)
            if role is not None:
                database.set_attr("guilds", f"{ctx.guild.id}.autorole", role.id)
                await ctx.send(f"Automatically assigned role for {ctx.guild.name} set to `@{role.name}`")
            else:
                await ctx.send("ERROR: Invalid role")

        elif mode == "levelup":
            if arg is not None:
                if arg.lower() == "true":
                    setting = True
                elif arg.lower() == "false":
                    setting = False
                else:
                    await ctx.send(f"ERROR: Invalid setting `{arg}`. Please give `true` or `false`")
                    return
                database.set_attr("guilds", f"{ctx.guild.id}.levelup_messages", setting)
                await ctx.send(f"Levelup messages are now `{'on' if setting else 'off'}` on this server")
            else:
                await ctx.send(f"ERROR: Please give `true` or `false` to set this setting to")
        else:
            await ctx.send("Error: Please give a parameter to configure.\n"
                           "`[welcome | muterole | autorole | levelup]`")


def setup(client):
    client.add_cog(Mod(client))
