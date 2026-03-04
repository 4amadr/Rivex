from src.rivex.utils.requests_utils.requests import HttpRequisitions
from dotenv import load_dotenv
import os

class IpboxApi:
    def coleta_ipbox(self, data):
        load_dotenv
        token = os.getenv('IPBOX_TOKEN')