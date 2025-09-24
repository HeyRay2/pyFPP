import json
import requests
import requests.packages
import urllib3
from typing import List, Dict


# Class for a REST Adapter for the Falcon Player API
class FalconPlayerRestAdapter:
    def __init__(self, hostname: str, api_key: str = "", ssl_verify: bool = True, timeout: int = None):
        self.url = "http://{}/api/".format(hostname)
        self._api_key = api_key
        self._ssl_verify = ssl_verify
        self._request_timeout = timeout
        if not ssl_verify:
            urllib3.disable_warnings()
            # requests.packages.urllib3.disable_warnings()

    # Consolidated method for all request types
    def _do(self, http_method: str, endpoint: str, endpoint_params: Dict = None, data: Dict = None):
        full_url = self.url + endpoint
        headers = {'x-api-key': self._api_key}
        response = requests.request(
            method=http_method,
            url=full_url,
            verify=self._ssl_verify,
            headers=headers,
            params=endpoint_params,
            timeout=self._request_timeout)
        data_out = response.json()
        if 200 <= response.status_code <= 299:  # OK response
            return data_out
        raise Exception(data_out["message"])  # Will raise custom exceptions later

    # GET method for REST Adapter
    def get(self, endpoint: str, endpoint_params: Dict = None) -> List[Dict]:
        return self._do(http_method='GET', endpoint=endpoint, endpoint_params=endpoint_params)

    # POST method for REST Adapter
    def post(self, endpoint: str, endpoint_params: Dict = None, data: Dict = None) -> List[Dict]:
        return self._do(
            http_method='POST',
            endpoint=endpoint,
            endpoint_params=endpoint_params,
            data=data)

    # DELETE method for REST Adapter
    def delete(self, endpoint: str, endpoint_params: Dict = None, data: Dict = None):
        return self._do(
            http_method='DELETE',
            endpoint=endpoint,
            endpoint_params=endpoint_params,
            data=data)


# Class for Falcon Player
class FalconPlayer:
    def __init__(self, ip, logger, timeout) -> None:
        self.ip = ip
        self.logger = logger
        self.timeout = timeout
        self.hostname = None
        self.description = None
        self.platform = None
        self.variant = None
        self.version = None
        self.branch = None
        self.mode = None

        # Connect to Falcon Player
        self.__connect()

    def __connect(self):
        fpp_api = FalconPlayerRestAdapter(hostname=self.ip)
        fpp_api_endpoint = "system/info"

        self.logger.info("Querying for Falcon Player at '{}{}'".format(
            fpp_api.url,
            fpp_api_endpoint))

        fpp_response = fpp_api.get(fpp_api_endpoint)

        # Show response details
        self.logger.info(fpp_response)
        self.logger.debug(json.dumps(fpp_response))

        # Set player info
        response = fpp_response
        self.hostname = response.get("HostName")
        self.description = response.get("HostDescription")
        self.platform = response.get("Platform")
        self.variant = response.get("Variant")
        self.version = response.get("Version")
        self.branch = response.get("Branch")
        self.mode = response.get("Mode")

        # Log the Player details
        self.logger.info("Falcon Player found at '{}'\n{}".format(
            self.ip,
            self.to_dict()))

        return

    def to_dict(self):
        return {
            "hostname": self.hostname,
            "description": self.description,
            "platform": self.platform,
            "variant": self.variant,
            "version": self.version,
            "branch": self.branch,
            "mode": self.mode
        }
