from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QTextEdit,
    QVBoxLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
)

from ui import SidebarLabel
from models import Message
import commands

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject
    from models import (
        Chatter,
        RewardEvent,
        FollowEvent,
        SubscribeEvent,
        GiftSubEvent,
        ReSubscribeEvent,
        CheersEvent,
        RaidEvent,
        BanEvent,
    )
    from network import Client


class MessageTextBox(QLineEdit):
    def __init__(self, client: Client):
        super().__init__()
        self.client = client
        self.setReadOnly(True) if not self.client.streamer else ...
        self.returnPressed.connect(self.send)

    def setReadOnly(self, a0: bool) -> None:
        self.streamer = self.client.streamer if not a0 else None
        return super().setReadOnly(a0)

    def send(self) -> None:
        if not (message := self.text()):
            return
        self.client.send_message(message)
        self.clear()
        message = Message(0, self.client.streamer, message)
        if message.content.startswith("*"):
            msg = message.content.lstrip("*").split(" ")
            data = {"command": {"botCommand": msg[0], "botCommandParams": msg[1:]}}
            self.client.run_command(data, message)


class MessagePage(QFrame):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
        self.setContentsMargins(10, 10, 10, 6)
        self.setStyleSheet(
            "MessagePage {background-color: #1E1E1E; color: #FFFFFF; border: none;}"
        )

        self.text_edit = QTextEdit(self)
        self.text_edit.setStyleSheet(
            "QTextEdit {background-color: #1E1E1E; color: #FFFFFF; border: none;}"
        )
        self.text_edit.setReadOnly(True)

        self.textbox = MessageTextBox(self.client)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.text_edit)
        self._layout.addWidget(self.textbox)
        self.setLayout(self._layout)

    def append(self, text: str):
        self.text_edit.append(text)


class ChatterFrame(QFrame):
    def __init__(self, parent: QObject, chatter: Chatter) -> None:
        super().__init__(parent)
        self.img = QLabel(self)
        self.img.setPixmap(QPixmap("icons/twitch.png"))
        self.text = QLabel(self)
        self.text.setText(chatter.display_name)
        self.setStyleSheet(
            """
            ChatterFrame {
                background-color: #2C2C2C;
                border-width: 1px;
                border-style: solid;
                border-color: #2C2C2C;
                border-radius: 10px;
                margin: 10px 10px 6px 10px;
                font-size: 20px;
                font-weight: bold;
            }
            ChatterFrame > QLabel {
                background-color: #2C2C2C;
                border-width: 1px;
                border-style: solid;
                border-color: #2C2C2C;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            """
        )
        self.setMinimumSize(300, 100)
        self.setMaximumSize(300, 100)

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.img)
        layout.addWidget(self.text)
        self.setLayout(layout)


class ChattersList(QScrollArea):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
        self.setStyleSheet(
            "ChattersList {background-color: #1E1E1E; color: #FFFFFF; border: none;}"
        )

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Plain)
        self.frame.setStyleSheet(
            "QFrame {background-color: #1E1E1E; color: #FFFFFF; border: none;}"
        )
        self._layout = QGridLayout(self.frame)

        self.row, self.col = 0, 0

        self.frame.setLayout(self._layout)
        self._layout.setSpacing(0)
        self.setWidget(self.frame)
        self.setWidgetResizable(True)

    def add_chatter(self, chatter: Chatter):
        label = ChatterFrame(self, chatter)
        self._layout.addWidget(label, self.row, self.col, Qt.AlignmentFlag.AlignTop)
        self.col += 1
        if self.col == 3:
            self.row += 1
            self.col = 0


class ChattersPage(QFrame):
    def __init__(self, client: Client) -> None:
        super().__init__()
        self.client = client
        self.setContentsMargins(10, 10, 10, 6)
        self.setStyleSheet(
            "ChattersPage {background-color: #1E1E1E; color: #FFFFFF; border: none;}"
        )

        self.chatters_list = ChattersList(self.client)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self.chatters_list)
        self.setLayout(self._layout)

    def add_chatter(self, chatter: Chatter):
        self.chatters_list.add_chatter(chatter)


class ModView(commands.Cog):
    def __init__(self, client: Client) -> None:
        self.window = client.window
        self.client = client

        self.message_page = MessagePage(self.client)
        self.window.stack.addWidget(self.message_page)

        self.chatters_page = ChattersPage(self.client)
        self.window.stack.addWidget(self.chatters_page)

        sidebar = self.window.sidebar
        self.message_label = SidebarLabel(sidebar, self.message_page)
        self.message_label.setText("Messages")
        sidebar.addWidget(self.message_label)

        self.chatters_label = SidebarLabel(sidebar, self.chatters_page)
        self.chatters_label.setText("Chatters")
        sidebar.addWidget(self.chatters_label)

    def unload(self):
        self.window.stack.removeWidget(self.message_page)
        self.window.sidebar.removeWidget(self.message_label)
        self.window.stack.removeWidget(self.chatters_page)
        self.window.sidebar.removeWidget(self.chatters_label)

    @commands.event()
    def on_channel_join(self) -> None:
        self.message_page.textbox.setReadOnly(False)

    @commands.event()
    def on_channel_leave(self) -> None:
        self.message_page.textbox.setReadOnly(True)

    @commands.event()
    def on_chatter_join(self, chatter: Chatter):
        self.chatters_page.add_chatter(chatter)

    @commands.event()
    def on_follow_event(self, follow: FollowEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{follow.chatter.display_name} followed!!!</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_ban_event(self, ban: BanEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{ban.chatter.display_name} has been banned'
        if ban.timeout:
            msg += f" for {ban.timeout} seconds"
        msg += "</span>"
        self.message_page.append(msg)

    @commands.event()
    def on_raid_event(self, raid: RaidEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{raid.chatter.display_name} raided with {raid.viewers} people!!!</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_sub_event(self, sub: SubscribeEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{sub.chatter.display_name} subbed. They have been subbed for 1 month now!!!</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_gift_sub_event(self, sub: GiftSubEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{sub.chatter.display_name} gifted {sub.total} {sub.tier} subs!!!</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_resub_event(self, sub: ReSubscribeEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{sub.chatter.display_name} resubbed for {sub.duration_months}. They have been subbed for {sub.consecutive_months} now!!!</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_cheers_event(self, cheers: CheersEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{cheers.chatter.display_name} cheered with {cheers.bits} bits</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_reward_event(self, reward: RewardEvent):
        msg = f'<span style="font-weight:bold; color:#F2FA00;">{reward.chatter.display_name} redeemed {reward.reward.title}</span>'
        self.message_page.append(msg)

    @commands.event()
    def on_message(self, message: Message):
        msg = f'<span style="font-weight:600; color:{message.author.color};">{message.author.display_name}</span>: {message.content}'
        self.message_page.append(msg)


def setup(client: Client) -> ModView:
    return client.add_cog(ModView(client))
