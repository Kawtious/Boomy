import discord
from poke_env import Player
from poke_env.battle import AbstractBattle
from poke_env.player import BattleOrder


class DiscordRandomPlayer(Player):
    def __init__(self, message: discord.Message | None = None, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.reply = None

    async def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        move = self.choose_random_move(battle)

        if self.message is None:
            return move

        if self.reply is None:
            self.reply = await self.message.reply(
                content=str(battle)
            )
        else:
            await self.reply.edit(
                content=str(battle)
            )

        return move
