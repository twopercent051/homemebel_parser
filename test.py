import requests
from fake_useragent import UserAgent
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

url = 'https://mayamebel.ru/catalog/'
useragent = UserAgent()
headers = {
    "Accept": "*/*",
    "User-Agent": useragent.random
}
session = requests.Session()
retry = Retry(connect=100, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

req = session.get(url=url, headers=headers)

print(req)