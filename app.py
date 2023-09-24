from httpx import Client
from re import search
import queries


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
        # TODO - Padrão de requisição do GraphQL
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
        return data["chatOfBot"]["chatId"]

    def create_chat(self, bot: str = "chinchilla", message: str = ""):
        variables = {
            "bot": bot,
            "query": message,
            "source": {
                "sourceType": "chat_input",
                "chatInputMetadata": {
                    "useVoiceRecord": False,
                    "newChatContext": "chat_settings_new_chat_button",
                },
            },
            "sdid": "",
            "attachments": [],
        }
        query = queries.query_generate(
            "ChatHelpersSendNewChatMessageMutation", variables
        )
        response = self.main_request(json=query)
        return response["data"]["messageEdgeCreate"]["chat"]

    def send_msg(self, bot: str, message: str):
        chat_id = self.get_chat_id(bot)
        bot_response = []
        variables = {
            "bot": bot,
            "chatId": chat_id,
            "query": message,
            "source": {
                "sourceType": "chat_input",
                "chatInputMetadata": {"useVoiceRecord": False},
            },
            "withChatBreak": False,
            "clientNonce": None,
            "sdid": "",
            "attachments": bot_response,
        }
        query = queries.query_generate("SendMessageMutation", variables)
        response_json = self.main_request(json=query)
        # message_data = response_json["data"]["messageEdgeCreate"]["chat"]
        # return message_data

    def get_last_msg(self):
        query = """query ChatPaginationQuery($bot: String!, $before: String, $last: Int! = 10) {
                        chatOfBot(bot: $bot) {
                            id
                            __typename
                            messagesConnection(before: $before, last: $last) {
                                pageInfo {
                                    hasPreviousPage
                                }
                                edges {
                                    node {
                                        id
                                        __typename
                                        messageId
                                        text
                                        linkifiedText
                                        authorNickname
                                        state
                                        vote
                                        voteReason
                                        creationTime
                                        suggestedReplies
                                    }
                                }
                            }
                        }
                    }
                """
        variables = {"bot": "chinchilla", "before": None}
        query_data = {
            "operationName": "ChatPaginationQuery",
            "query": query,
            "variables": variables,
        }
        response_json = self.main_request(json=query_data)
        chatdata = response_json["data"]
        # edges = chatdata['messagesConnection']['edges'][::-1]
        return chatdata


poe_key = "Uz2ntD3I7GyrsW-33U_d0A%3D%3D"

poe = PoeAiGen(poe_key)
poe.send_msg(bot="chinchilla", message="Olá, Boa Noite?")
print(poe.get_last_msg())
