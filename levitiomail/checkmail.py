import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import discord

import base64
import subprocess
import regex

from sqlitedict import SqliteDict

import html2text

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://mail.google.com/"]

CRED_TOKEN = "persistent/credentials/mail_token.json"
CRED_CRED = "persistent/credentials/mail_credentials.json"
USER_LINK_DB = "persistent/data/levitio_links.db"
PERSONAL_TIMEOUT = 30


h2t = html2text.HTML2Text()
h2t.ignore_images = True
h2t.body_width = 0
h2t.ignore_tables = True
h2t.single_line_break = True
h2t.ignore_mailto_links = True


class SignUpButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Přihlásit se v Levitiu", custom_id="SignUpButton_0000",
                       row=0, style=discord.ButtonStyle.primary)
    async def signup_callback(self, interaction, button):

        uid = interaction.user.id
        # print(uid)
        with SqliteDict(USER_LINK_DB) as db:
            # print(len(db))
            link = db.get(uid)

        if link is not None:
            await show_signup_link(interaction, link)
        else:
            await interaction.response.send_modal(LevitioSignupModal(user_id="", title="Přihlásit se v Levitiu"))

async def show_signup_link(interaction, link):
    await interaction.response.send_message(
        "Tady se můžeš přihlásit nebo změnit nastavení.",
        # "[Klikni sem pro tvůj Levitio přehled](https://public.levitio.com/units/dcbf1eb0-cd5f-49dd-bb6c-2e8f8743a35f?email=foton.web@stezka.org&verification=6f667d6667277e6c6b497a7d6c73626827667b6e) .",
        view=PersonalSignupView(link),
        ephemeral=True, delete_after=PERSONAL_TIMEOUT, suppress_embeds=True,
    )

class PersonalSignupView(discord.ui.View):
    def __init__(self, link):
        super().__init__(timeout=PERSONAL_TIMEOUT)

        b1 = discord.ui.Button(
            label='Tvůj Levitio přehled',
            url=link
        )
        self.add_item(b1)

        b2 = SettingsButton(
            label="⚙",
            style=discord.ButtonStyle.red,
        )
        self.add_item(b2)

class SettingsButton(discord.ui.Button):
    async def callback(self, interaction):
        await interaction.response.send_modal(LevitioSignupModal(user_id="", title="Přihlásit se v Levitiu"))

class LevitioSignupModal(discord.ui.Modal):
    def __init__(self, user_id, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        desctext = "Aby toto tlačítko fungovalo, potřebujeme odkaz na tvůj Levitio přehled. (Klikni na libovolnou pozvánku z e-mailu -> pravým tlačítkem na Přehled akcí (vlevo) -> kopírovat adresu odkazu) Jakmile ho jednou zadáš do následujícího políčka, E-Pip si ho zapamatuje a bude ti stačit jenom kliknout sem; nebudeš muset chodit na e-mail."

        self.add_item(discord.ui.TextInput(
            label="Vysvětlení",
            default=desctext,
            required=False,
            style=discord.TextStyle.long,
        ))

        self.new_link_input = discord.ui.TextInput(
            label="Odkaz na tvůj Levitio přehled",
            # style=discord.TextStyle.,
            required=True,
        )
        self.add_item(self.new_link_input)


    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        link = self.new_link_input.value
        # print(uid)
        # print(self.new_link_input.value)

        warning = ""
        if not link.startswith("https://public.levitio.com/units/"):
            warning="\n\nZdá se mi, že by ten odkaz měl vypadat jinak. Zkopíroval jsi správný odkaz?\nKdyžtak si ho můžeš změnit opětovným kliknutím na \"Přihlásit se v Levitiu\" -> Nastavení (⚙)."

        if link.startswith("http"):
            print(f"Remembering for {uid}: {self.new_link_input.value}")
            with SqliteDict(USER_LINK_DB) as db:
                db[uid] = self.new_link_input.value
                db.commit()

            await interaction.response.send_message(
                f'Zapamatoval jsem si tvůj [odkaz]({self.new_link_input.value}).' + warning,
                ephemeral=True, delete_after=PERSONAL_TIMEOUT, suppress_embeds=True,
            )
        else:
            await interaction.response.send_message(
                warning,
                ephemeral=True, delete_after=PERSONAL_TIMEOUT, suppress_embeds=True,
            )


async def post_email(data, channel):
    text = convert_mail(data)
    embed = discord.Embed(
        # title="Sample Embed",
        # url="https://realdrewdata.medium.com/",
        description=text,
        color=0xFF5733,
    )
    await channel.send(
        embed=embed,
        view=SignUpButton()
    )

def convert_mail(html):
    # with open("mail.html", "w") as f:
    #     f.write(html)
    # subprocess.check_output(
    #     ["/home/peta/.local/bin/html2text", "--ignore-images", "-b", "0", "--ignore-tables", "--single-line-break", "--ignore-mailto-links"],
    #     input=html,
    #     encoding="utf-8",
    # )

    converted = h2t.handle(html)
    if "* * *" in converted:
        converted = converted.split("* * *")[0]
    # converted = converted.replace(" **", "**")
    converted = converted.replace("****", "** **")
    converted = converted.replace("\n  *", "\n-")
    converted = converted.replace("**S sebou:**", "\n**S sebou:**")
    converted = converted.replace("\n\n\n", "\n\n")
    converted = converted.replace("**Hlavní vedoucí:**\n", "**Hlavní vedoucí:** ")
    converted = converted.strip()

    m = regex.search(r"\[Potvrdit či omluvit účast\].*", converted)
    if m:
        signup = m.group(0)
        l, r = m.span()
        converted = converted[:l] + converted[r:]

    # converted = regex.sub(r"(?=[\S])\*\*", " **", converted)

    # converted += "\n\n## *Nezapomeňte se přihlásit na vašem e-mailu!*"
    return converted

async def check_emails(channel):
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists(CRED_TOKEN):
    creds = Credentials.from_authorized_user_file(CRED_TOKEN, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          CRED_CRED, SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(CRED_TOKEN, "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)

    query="from:info@levitio.com label:unread"
    results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
    # print(results)

    messages = results.get("messages", [])

    if not messages:
        # print("You have no New Messages.")
        return

    for message in results["messages"][::-1]:
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()

        for p in msg["payload"]["parts"]:
            # print(p["mimeType"])
            if p["mimeType"] in ["text/html"]:
                data = base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8")
                await post_email(data, channel)

        # mark as read
        service.users().messages().modify(
            userId='me', id=message["id"], body={'removeLabelIds': ['UNREAD']}).execute()

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
