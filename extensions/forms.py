## -- IMPORTING -- ##

# MODULES
import disnake

from disnake.ext import commands
from dotenv import load_dotenv

# FILES
from utils.checks import is_staff
from utils.data import GuildData


## -- VARIABLES -- ##

load_dotenv()

## -- FUNCTIONS -- ##


## -- COG -- ##


class Forms(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ## -- SLASH COMMANDS -- ##

    @commands.slash_command(name="forms")
    async def forms(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms.sub_command(name="create")
    async def forms_create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str,
        type: commands.option_enum(["application", "questionare", "other"]),
    ):
        """Create a form of the given name and type.
        Parameters
        ----------
        name: What name you want to assign to the form.
        type: The type of form you're looking to create.
        """
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms.sub_command(name="edit")
    async def forms_edit(self, inter: disnake.ApplicationCommandInteraction, form: str):
        """Edit the given form.
        Parameters
        ----------
        form: The form you're looking to edit.
        """
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms.sub_command(name="delete")
    async def forms_delete(self, inter: disnake.ApplicationCommandInteraction, form: str):
        """Delete a form of the given name.
        Parameters
        ----------
        form: The form you're looking to delete.
        """
        pass

    @forms.sub_command(name="start")
    async def forms_start(self, inter: disnake.ApplicationCommandInteraction, form: str):
        """Start an interactive form in your DMs.
        Parameters
        ----------
        form: The form you're looking to do.
        """
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms.sub_command(name="enable")
    async def forms_enable(self, inter: disnake.ApplicationCommandInteraction, form: str):
        """Enables a disabled form, allowing it to be done.
        Parameters
        ----------
        form: The form to enable.
        """
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms.sub_command(name="disable")
    async def forms_disable(self, inter: disnake.ApplicationCommandInteraction, form: str):
        """Disables a form temporarily, preventing it from being done.
        Parameters
        ----------
        form: The form to disable.
        """
        pass

    @forms.sub_command(name="view")
    async def forms_view(self, inter: disnake.ApplicationCommandInteraction, form: str):
        """Views information on the given form.
        Parameters
        ----------
        form: The form to view.
        """
        pass

    @forms.sub_command_group(name="limits")
    async def forms_limits(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms_limits.sub_command(name="add")
    async def forms_limits_add(
        self, inter: disnake.ApplicationCommandInteraction, form: str, limiter: disnake.Role | disnake.Member
    ):
        """Limits a form to the specified role or member.
        Parameters
        ----------
        form: The form to edit.
        limiter: What role or member to limit this form to.
        """
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms_limits.sub_command(name="remove")
    async def forms_limits_remove(
        self, inter: disnake.ApplicationCommandInteraction, form: str, limiter: disnake.Role | disnake.Member
    ):
        """Limits a form to the specified role or member.
        Parameters
        ----------
        form: The form to edit.
        limiter: What role or member to limit this form to.
        """
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms_limits.sub_command(name="clear")
    async def forms_limits_clear(self, inter: disnake.ApplicationCommandInteraction, form: str):
        pass

    @is_staff(type="administrator", manage_guild=True, administrator=True)
    @forms_limits.sub_command(name="view")
    async def forms_limits_view(self, inter: disnake.ApplicationCommandInteraction, form: str):
        pass

    ## -- AUTOCOMPLETERS -- ##

    @forms_edit.autocomplete("form")
    @forms_delete.autocomplete("form")
    @forms_start.autocomplete("form")
    @forms_enable.autocomplete("form")
    @forms_disable.autocomplete("form")
    @forms_limits_add.autocomplete("form")
    @forms_limits_remove.autocomplete("form")
    @forms_limits_clear.autocomplete("form")
    @forms_limits_view.autocomplete("form")
    @forms_view.autocomplete("form")
    async def form_autocompleter(self, inter: disnake.ApplicationCommandInteraction, input: str):
        guild_data_obj = GuildData(inter.guild.id)
        guild_data = guild_data_obj.get_data()
        forms = guild_data["forms"]

        return [form for form in forms if input.lower() in forms["name"].lower()]


def setup(bot):
    bot.add_cog(Forms(bot))
