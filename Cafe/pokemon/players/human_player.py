import asyncio

import discord
from poke_env import Player, ServerConfiguration
from poke_env.battle import AbstractBattle
from poke_env.player import BattleOrder
from vault.data.database.user import User


class HumanPlayer(Player):
    def __init__(
            self,
            user: User,
            server_config: ServerConfiguration,
            interaction: discord.Interaction,
            **kwargs
    ):
        super().__init__(
            server_configuration=server_config,
            **kwargs
        )
        self.__team = user.pokemon.data
        self.user = user
        self.interaction = interaction
        self.__pending_choice: asyncio.Future = asyncio.Future()

    async def choose_move(self, battle: AbstractBattle) -> BattleOrder:
        if self.__pending_choice.done():
            self.__pending_choice = asyncio.Future()
        await self.prompt_moves(battle)
        return await self.__pending_choice

    def set_choice(self, choice):
        if not self.__pending_choice.done():
            self.__pending_choice.set_result(choice)

    async def prompt_moves(self, battle: AbstractBattle):
        moves = battle.available_moves
        if not moves:
            # Struggle fallback
            self.set_choice(battle.available_moves[0])
            return

        view = discord.ui.View()
        for move in moves:
            button = discord.ui.Button(label=f"{move.id} ({move.base_power})")

            async def callback(interaction: discord.Interaction, move=move):
                if interaction.user.id != self.user.id:
                    await interaction.response.send_message("Not your turn!", ephemeral=True)
                    return
                self.set_choice(move)
                await interaction.response.edit_message(content=f"You chose **{move.id}**!", view=None)

            button.callback = callback
            view.add_item(button)
        await self.interaction.followup.send(f"Your move choices, {self.user.display_name}:", view=view, ephemeral=True)
