import discord
from discord.ext import commands
from utils import misc as misomisc
from utils import logger as misolog
from utils import plotter
import time as t
from operator import itemgetter
import main

database = main.database


class Levels(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.logger = misolog.create_logger(__name__)

    @commands.is_owner()
    @commands.command(name="index")
    async def index_messages(self, ctx, arg=None):
        """Index the server for past level stats"""
        self.logger.info(misolog.format_log(ctx, f""))
        if ctx.author.id not in [133311691852218378]:
            await ctx.send(f"You are not authorized to use this command")
            return
        timer = t.time()
        if arg == "server":
            channels = ctx.guild.text_channels
        else:
            channels = [ctx.channel]
        msg = await ctx.send(f"indexing... (0/{len(channels)})")
        num = 0
        guild_index = {}
        total_messages = 0
        for channel in channels:
            num += 1
            try:
                messages = await channel.history(limit=None).flatten()
                for message in messages:
                    user = message.author
                    xp = misomisc.xp_from_message(message)
                    currenthour = message.created_at.hour
                    if str(user.id) not in guild_index:
                        guild_index[str(user.id)] = {
                            "name": f"{user.name}#{user.discriminator}",
                            "bot": user.bot,
                            "xp": xp,
                            "messages": 1,
                            "activity": [0] * 24}
                    else:
                        guild_index[str(user.id)]['xp'] += xp
                        guild_index[str(user.id)]['messages'] += 1
                        guild_index[str(user.id)]['activity'][currenthour] += xp
                        total_messages += 1

                await msg.edit(content=f"indexing... ({num}/{len(channels)}) :: total {total_messages} messages from "
                                       f"{len(guild_index)} users")
            except Exception as e:
                self.logger.error(misolog.format_log(ctx, e))
                await ctx.send(f"Unexpected error indexing channel <#{channel.id}>")
        time_taken = t.time() - timer
        database.set_attr("index", f"{ctx.guild.id}", guild_index)
        await msg.edit(content=f"indexing... ({num}/{len(channels)}) DONE ({time_taken:.1f}s) :: "
                               f"total {total_messages} messages from {len(guild_index)} users")

    @commands.command(alias=["ranks", "levels"])
    async def toplevels(self, ctx, scope=None):
        """Get top levels for this server or globally"""
        self.logger.info(misolog.format_log(ctx, f""))
        tops = {}
        for guild in database.get_attr("index", "."):
            if not scope == "global":
                guild = str(ctx.guild.id)
            for userid in database.get_attr("index", f"{guild}"):
                userdata = database.get_attr("index", f"{guild}.{userid}")
                if userid not in tops:
                    tops[userid] = {'xp': userdata['xp'], 'messages': userdata['messages']}
                else:
                    tops[userid]['xp'] += userdata['xp']
                    tops[userid]['messages'] += userdata['messages']
            if not scope == "global":
                break

        if not scope == "global":
            content = discord.Embed(title=f"{ctx.guild.name} levels leaderboard")
        else:
            content = discord.Embed(title=f"Global levels leaderboard")

        content.description = ""
        i = 0

        for userid, value in sorted(tops.items(), key=lambda x: itemgetter('xp')(x[1]), reverse=True):
            if scope == "global":
                user = self.client.get_user(int(userid))
            else:
                user = ctx.guild.get_member(int(userid))
            if user is None or user.bot:
                continue
            i += 1
            row = f"\n{i}. Level **{misomisc.get_level(tops[userid]['xp'])}** - {user.mention} " \
                  f"| **{tops[userid]['xp']}** XP - **{tops[userid]['messages']}** messages"
            if len(content.description) + len(row) < 2000:
                content.description += row
            else:
                break
        await ctx.send(embed=content)

    @commands.command(aliases=["level", "rank"])
    async def activity(self, ctx, mention=None):
        self.logger.info(misolog.format_log(ctx, f""))
        if mention is not None:
            user = misomisc.user_from_mention(ctx.guild, mention, ctx.author)
            if user is None:
                user = ctx.author
        else:
            user = ctx.author

        post_data = database.get_attr("index", f"{ctx.guild.id}.{user.id}.activity")
        if post_data is None:
            await ctx.send("You have no activity data yet!")
            return

        userdata = database.get_attr("index", f"{ctx.guild.id}.{user.id}")
        level = misomisc.get_level(userdata['xp'])

        title = f"Level {level} | {userdata['xp'] - misomisc.get_xp(level)} / " \
                f"{misomisc.xp_to_next_level(level)} XP to next level\nTotal xp: {userdata['xp']}"

        plotter.create_graph(post_data, str(user.color), title=title)

        try:
            with open("downloads/graph.png", "rb") as img:
                await ctx.send(file=discord.File(img))
        except Exception:
            chart_rows, num_rows = misomisc.generate_graph(post_data, 5, 15)
            # chart_rows[0] = chart_rows[0] + (f" {max(post_data)} xp" if max(post_data) > 15 else f" 15 xp")
            # chart_rows[-1] = chart_rows[-1] + " 0 xp"
            chart = " \n".join(chart_rows) + "\n" + "\n".join(num_rows)
            graph = f"{chart}"
            content = discord.Embed()
            content.set_author(name=f"{user.name}'s hourly xp gain graph",
                               icon_url=user.avatar_url)

            content.description = f"{title}\n```{graph}```"
            await ctx.send(embed=content)


def setup(client):
    client.add_cog(Levels(client))
