import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands
import os
import logging
from datetime import datetime, timezone, timedelta

# Configuration du logger
logger = logging.getLogger('bot.clear_module')
# logging.basicConfig(level=logging.INFO)

# Variables d'environnement pour la configuration
moderator_role_ids_str = os.getenv('MODERATOR_ROLE_IDS', '')

# Parsing des IDs de rôles modérateurs
if moderator_role_ids_str:
    try:
        moderator_role_ids = list(map(int, moderator_role_ids_str.split(',')))
    except ValueError:
        logger.error("La variable d'environnement 'MODERATOR_ROLE_IDS' contient des valeurs invalides.")
        moderator_role_ids = []
else:
    moderator_role_ids = []
    logger.warning("La variable d'environnement 'MODERATOR_ROLE_IDS' est vide ou non définie.")

class ClearMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_moderator(self, member):
        return any(role.id in moderator_role_ids for role in member.roles)

    @nextcord.slash_command(name="clear", description="Supprimer un nombre spécifique de messages.")
    async def clear(self,
                    interaction: Interaction,
                    number: int = SlashOption(name="number", description="Nombre de messages à supprimer", required=True, min_value=1, max_value=100),
                    member: nextcord.Member = SlashOption(name="member", description="Membre visé (facultatif)", required=False)):
        # Vérifier les permissions
        if not await self.is_moderator(interaction.user):
            await interaction.response.send_message("Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
            return
        
        await interaction.response.defer()

        # Identifier l’ID du message de suivi
        followup_message = await interaction.followup.send("Suppression des messages en cours...", wait=True)
        followup_message_id = followup_message.id

        # Définir la limite de suppression des messages (14 jours)
        time_limit = datetime.now(timezone.utc) - timedelta(weeks=2)
        deleted_messages = 0

        if member:
            # Supprimer les messages d'un utilisateur spécifique
            def check(msg):
                # Ne pas supprimer le message de suivi
                return msg.author.id == member.id and msg.created_at > time_limit and msg.id != followup_message_id

            async for message in interaction.channel.history(limit=200).filter(check):
                if deleted_messages < number:
                    await message.delete()
                    deleted_messages += 1
                else:
                    break
        else:
            # Supprimer les derniers messages
            async for message in interaction.channel.history(limit=number):
                # Ne pas supprimer le message de suivi ou le message d'interaction ou les messages trop vieux
                if message.id != interaction.id and message.created_at > time_limit and message.id != followup_message_id: 
                    await message.delete()
                    deleted_messages += 1

        # Editer le message de suivi avec le nombre de messages supprimés
        await followup_message.edit(content=f"{deleted_messages} messages supprimés.")

def setup(bot):
    bot.add_cog(ClearMessages(bot))
