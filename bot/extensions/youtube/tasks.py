import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO

import discord
import requests
from discord.ext import commands, tasks
from PIL import Image
from pydantic import BaseModel

from bot import core
from bot.config import settings
from bot.services import http

YOUTUBE_URL = re.compile(r"(?P<url>https?://www\.youtube\.com/watch\?v=[\w-]+)")


class Video(BaseModel):
    link: str
    title: str
    published: str
    description: str
    thumbnail: str


class YoutubeTasks(commands.Cog):
    """Tasks for YouTube functions"""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.video_links: list[str] = []
        self.check_for_new_videos.start()

    def cog_unload(self) -> None:
        self.check_for_new_videos.cancel()

    @property
    def channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.notification.channel_id)

    def crop_borders(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to download the image.")

        img = Image.open(BytesIO(response.content))
        width, height = img.size

        img_cropped = img.crop((0, 45, width, height - 45))

        buf = BytesIO()
        img_cropped.save(buf, format="PNG")
        buf.seek(0)
        return buf

    async def send_notification(self, video: Video) -> None:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.crop_borders, video.thumbnail)
        file = discord.File(fp=result, filename="thumbnail.png")

        embed = discord.Embed(
            title=video.title,
            description=video.description.split("\n\n")[0],
            url=video.link,
            color=discord.Color.red(),
            timestamp=datetime.strptime(video.published, "%Y-%m-%dT%H:%M:%S%z"),
        )
        embed.set_image(url="attachment://thumbnail.png")
        embed.set_author(
            name="Tech With Tim",
            url="https://www.youtube.com/c/TechWithTim",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_footer(text="Uploaded", icon_url=self.bot.user.display_avatar.url)

        await self.channel.send(
            content=f"Hey <@&{settings.notification.role_id}>, **Tim** just posted a video! Go check it out!",
            file=file,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    @tasks.loop(minutes=2)
    async def check_for_new_videos(self):
        """Check for new videos"""

        url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4JX40jDee_tINbkjycV4Sg"
        async with http.session.get(url) as response:
            data = await response.text()
            tree = ET.fromstring(data)
            ns = "{http://www.w3.org/2005/Atom}"
            md = "{http://search.yahoo.com/mrss/}"

            entry = tree.find(ns + "entry")
            media_group = entry.find(md + "group")
            video = Video(
                link=entry.find(ns + "link").attrib["href"],
                title=entry.find(ns + "title").text,
                published=entry.find(ns + "published").text,
                description=media_group.find(md + "description").text,
                thumbnail=media_group.find(md + "thumbnail").attrib["url"],
            )

        if video.link in self.video_links:
            return

        self.video_links.append(video.link)
        await self.send_notification(video)

    @check_for_new_videos.before_loop
    async def before_check(self):
        if not self.video_links:
            async for message in self.channel.history(limit=10):
                if message.embeds:
                    self.video_links.append(message.embeds[0].url)
                else:
                    match = YOUTUBE_URL.search(message.content)
                    if match:
                        self.video_links.append(match.group("url"))

            self.video_links.reverse()