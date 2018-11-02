from bs4 import BeautifulSoup as bs
import requests

toc_url = 'https://eresearch.fidelity.com/eresearch/markets_sectors/PerformanceSector.jhtml'

response_sectors = requests.get(toc_url)
print(toc_url)
if not response_sectors.status_code  == 200:
    print("Failure to connect Fidelity Sectors")

results_sectors = bs(response_sectors.text,'html.parser')

sectors = results_sectors.find_all(class_='sector-heading')

for item in sectors:
    print(item.find('a')['href'])


