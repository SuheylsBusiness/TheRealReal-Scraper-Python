import os
import requests
from requests.auth import HTTPProxyAuth
from getpass import getuser
from urllib.parse import urlsplit
import datetime

class RestResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.content = response.content
        self.request = response.request

def do_request(url, header_type, req_method, req_body="", use_proxy=False):
    headers = add_headers(header_type, req_body)
    proxies = {}
    if use_proxy:
        proxies = {
            "http": "http://user-spjles9k99-asn-3320-os-android:test123@gate.smartproxy.com:7000",
            "https": "http://user-spjles9k99-asn-3320-os-android:test123@gate.smartproxy.com:7000",
        }
    response = requests.request(req_method, url, headers=headers, proxies=proxies, data=req_body)
    log_response(response, url)
    return RestResponse(response)

def add_headers(header_type, req_body):
    skip_headers = ["content-length", "host"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; sdk_gphone64_x86_64 Build/TPB4.220624.004; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.74 Mobile Safari/537.36 Upwork Android/1.46.3 (Client)"
    }
    current_dir = os.path.dirname(os.path.abspath(__file__))
    header_file_path = os.path.join(current_dir, "Misc", "ApiCookies", f"{header_type}.txt")
    if os.path.exists(header_file_path):
        with open(header_file_path, 'r') as f:
            for line in f:
                key, value = map(str.strip, line.split(':', 1))
                if not any(header in key.lower() for header in skip_headers):
                    headers[key] = value
    if req_body:
        headers["Content-Type"] = "application/json"
    return headers

def log_response(response, url):
    log_level = '\033[93m' if response.status_code != 200 else '\033[92m'
    print(f"{log_level}({datetime.datetime.now().strftime('%H:%M:%S')}): HTTP-REQUEST-PARAMETERS => httpMethod = {response.request.method} | url = {url[:min(len(url), 75)]} | Response = {response.content[:min(len(response.content), 350)]}\033[0m")

def get_headers_dict(header_type):
    headers = add_headers(header_type, "")
    return headers