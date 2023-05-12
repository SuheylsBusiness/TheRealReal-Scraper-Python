import os
import json
import aiohttp
import asyncio
from loguru import logger
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from handle_database.firesore import upload_data, retrieve_data, delete_data
from handle_database.storage_connector import CloudStorageConnector
import sys 
from custom_request import get_headers_dict
from aiohttp_proxy import ProxyConnector

TAXONOMY_ID = "329"

async def load_proxies(file_path):
    with open(file_path, "r") as proxies_file:
        proxies = proxies_file.read().splitlines()
    return proxies

async def fetch_products(session, url, headers, json_payload, all_products):
    try:
        async with session.post(url, json=json_payload, headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                product_array = response_data["data"]["products"]["edges"]

                for product in product_array:
                    images = [image["url"] for image in product["node"]["images"]]

                    attributes = {}
                    for attribute in product["node"]["attributes"]:
                        label = attribute["label"]
                        values = attribute["values"]
                        attributes[label] = values

                    color = attributes.get("Color", ["N/A"])
                    size = attributes.get("Clothing Size", ["N/A"])[0]
                    condition = attributes.get("Condition", ["N/A"])[0]

                    all_products.append({
                        "URL": "",
                        "ItemID": product["node"]["id"],
                        "Name": product["node"]["name"],
                        "Images": images,
                        "Price": product["node"]["price"]["final"]["formatted"],
                        "Brand": product["node"]["brand"]["name"],
                        "Size": size,
                        "SizeCategory": [],
                        "InseamMeasurementInches":"",
                        "RiseMeasurementInches":"",
                        "WaistMeasurementInches":"",
                        "Rise":"",
                        "PantCut":"",
                        "NewWithTags":"",
                        "JeanWash":[],
                        "NumberFavorites":0,
                        "Material":[],
                        "Pattern":[],
                        "Accents":[],
                        "Tags":[],
                        "SellThroughScore":0,
                        "SearchTags":[],
                        "Color": color,
                        "Condition": condition
                    })
            else:
                print(f"Unexpected status code {response.status}")
                logger.error(f"Unexpected status code {response.status}")
    except Exception as e:
        print(f"Error when making request: {e}")
        logger.error(f"Error when making request: {e}")

async def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    proxies_file_path = os.path.join(current_directory, "Misc", "proxies.txt")
    proxy = (await load_proxies(proxies_file_path))[0]
    fetch_products_json_file_path = os.path.join(current_directory, "Misc", "RequestBodys", "TheRealReal - FetchProductsWith.json")
    with open(fetch_products_json_file_path, "r") as fetch_products_file:
        fetch_products_json_file = json.load(fetch_products_file)

    fetch_products_json_file["variables"]["after"] = None
    fetch_products_json_file["variables"]["where"]["buckets"]["taxons"] = [TAXONOMY_ID]

    firebase_admin.initialize_app()
    db = firestore.client()
    cloud_storage_connector = CloudStorageConnector()

    all_products = []
    headers =get_headers_dict("TheRealReal")

    connector = ProxyConnector.from_url(proxy)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            try:
                async with session.post(
                    "https://api.therealreal.com/graphql",
                    json=fetch_products_json_file,
                    headers=headers
                ) as response:
                    await fetch_products(session, "https://api.therealreal.com/graphql", headers, fetch_products_json_file, all_products)
                    fetch_products_content = await response.json()
                    next_cursor = fetch_products_content["data"]["products"]["pageInfo"]["endCursor"]
                    fetch_products_json_file["variables"]["after"] = next_cursor
                    hasNextPage = fetch_products_content["data"]["products"]["pageInfo"]["hasNextPage"]
                    if not hasNextPage:
                        break
            except Exception as e:
                print(f"Error when making request: {e}")
                logger.error(f"Error when making request: {e}")

    upload_data(db, all_products)
    cloud_storage_connector.insertToStorage(all_products, "bucket_name", "all_products.json")

logger.remove()
logger.add(sys.stderr, level="INFO")  # Adjust the logging level as needed
if __name__ == "__main__":
    asyncio.run(main())