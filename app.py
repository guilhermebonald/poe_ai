from httpx import Client
import json
from pathlib import Path
from re import search

# parent_path = Path(__file__).resolve().parent
# queries_path = parent_path / "queries.json"

# queries = json.loads(queries_path.read_text())


class PoeAiGen:
    URL_BASE = "https://pt.quora.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": '"Not.A/Brand";v="8", "Chromium";v="112"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Upgrade-Insecure-Requests": "1",
    }
    FORMKEY_PATTERN = r'formkey": "(.*?)"'

    def __init__(self, cookie: str):
        self.client = Client(base_url=self.URL_BASE, timeout=5)
        self.client.cookies.set("m-b", cookie)
        self.client.headers.update(
            {
                **self.HEADERS,
                "Quora-Formkey": self.get_formkey(),  # FormKey é gerado dinamicamente cada vez que a página é solicitada.
            }
        )

    def get_formkey(self):
        # Captura o código fonte da página e coleta e faz uma busca pelo FormKey
        response = self.client.get(
            self.URL_BASE, headers=self.HEADERS, follow_redirects=True
        )
        formkey = search(self.FORMKEY_PATTERN, response.text)[1]
        return formkey

    def main_request(self, json: dict):
        response = self.client.post(url=f"{self.URL_BASE}/poe_api/gql_POST", json=json)
        return response.json()

    def get_chat_id(self, bot: str):
        query = """
            query ChatViewQuery($bot: String!) {
                chatOfBot(bot: $bot) {
                    id
                    chatId
                    defaultBotNickname
                    shouldShowDisclaimer
                }
            }
        """
        variables = {"bot": bot}
        query_data = {
            "operationName": "ChatViewQuery",
            "query": query,
            "variables": variables,
        }
        response = self.main_request(json=query_data)
        data = response.get("data")
        return data['chatOfBot']['chatId']


    def send_msg(self, bot: str, message: str):
        query = f"""
            mutation AddHumanMessageMutation($chatId: BigInt!, $bot: String!, $query: String!, $source: MessageSource, $withChatBreak: Boolean! = false) {{
                messageCreate(
                    chatId: $chatId
                    bot: $bot
                    query: $query
                    source: $source
                    withChatBreak: $withChatBreak
                ) {{
                    __typename
                    message {{
                        __typename
                        ...MessageFragment
                        chat {{
                            __typename
                            id
                            shouldShowDisclaimer
                        }}
                    }}
                    chatBreak {{
                        __typename
                        ...MessageFragment
                    }}
                }}
            }}
        """
        chat_id = self.get_chat_id(bot)
        variables = {"chatId": chat_id, "bot": bot, "query": message, "source": False}
        query_data = {
            "operationName": "ChatViewQuery",
            "query": query,
            "variables": variables,
        }
        response = self.main_request(json=query_data)
        return response



poe_key = "Uz2ntD3I7GyrsW-33U_d0A%3D%3D"
quora_key = "3Wip-QviyZVPh0ZHgnRdzQ=="

print(PoeAiGen(poe_key).send_msg(bot="chinchilla", message='Olá Mundo'))
