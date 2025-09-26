import json
import logging
import requests
import requests.packages
import urllib3
from typing import List, Dict


# Class for Falcon Player API endpoints
class FalconPlayerApiEndpoint:
    def __init__(self, name: str = "", path: str = "", params: Dict = None, method: str = "GET"):
        """
        Constructor for a Falcon Player API endpoint
        :param name: The name of the endpoint
        :param path: The path for the endpoint
        :param params: The parameters for the endpoint
        :param method: The HTTP method for the endpoint
        """
        self.name = name,
        self.path = path,
        self.params = params,
        self.method = method


# Class for Falcon Player API endpoint categories
class FalconPlayerApiCategory:
    def __init__(self, name: str = ""):
        """
        Constructor for a Falcon Player API endpoint category
        :param name: The name of endpoint category
        """
        self.name = name
        self.endpoints = {}

        def add_endpoint(endpoint: FalconPlayerApiEndpoint):
            self.endpoints[endpoint.name] = endpoint

            return

        def get_endpoint(endpoint_name: str = ""):
            try:
                return self.endpoints[endpoint_name]
            except Exception as e:
                raise FalconPlayerApiException("Error retrieving endpoint") from e


# Class for responses from the Falcon Player API
class FalconPlayerApiResult:
    def __init__(self, status_code: int, message: str = '', data: List[Dict] = None):
        self.status_code = int(status_code)
        self.message = str(message)
        self.data = data if data else []


# Class for exception generated from errors returned by the Falcon Player API
class FalconPlayerApiException(Exception):
    pass


# Class for a REST Adapter for the Falcon Player API
class FalconPlayerRestAdapter:
    def __init__(
            self,
            hostname: str = 'fpp.local',
            api_key: str = "",
            ssl_verify: bool = True,
            timeout: int = None,
            logger: logging.Logger = None):
        """
        Constructor for FalconPlayerRestAdapter
        :param hostname: The IP address or hostname for the Falcon Player (Default: fpp.local)
        :param api_key: (optional) The string used for authentication for HTTP requests
        :param ssl_verify: SSL/TLS certificate validation (Default: True)
        :param timeout: The timeout period, in seconds, for the HTTP request
        :param logger: (optional) Pass an existing logger to the constructor
        """
        self.url = "http://{}/api/".format(hostname)
        self._api_key = api_key
        self._ssl_verify = ssl_verify
        self._request_timeout = timeout
        self._logger = logger or logging.getLogger(__name__)
        if not ssl_verify:
            urllib3.disable_warnings()
            # requests.packages.urllib3.disable_warnings()

    def _do(
            self,
            http_method: str,
            endpoint: str,
            endpoint_params: Dict = None,
            data: Dict = None) -> FalconPlayerApiResult:
        """
        Consolidated method for all HTTP requests
        :param http_method: The method for the request (GET, POST, DELETE, etc...)
        :param endpoint: The endpoint string for the HTTP request (example: system/info)
        :param endpoint_params: (optional) Parameters to pass along with the request
        :param data: (optional) The data payload for the request
        :return: Response from the API endpoint, cast as a FalconPlayerApiResult object
        """
        full_url = self.url + endpoint
        headers = {'x-api-key': self._api_key}

        log_line_pre = "method={}, url={}, params={}".format(
            http_method, full_url, endpoint_params)
        log_line_post = ', '.join((log_line_pre, "status={}, status_code={}, message={}"))

        # Log and perform an HTTP request, catch and raise any exceptions
        try:
            self._logger.debug(msg=log_line_pre)
            response = requests.request(
                method=http_method,
                url=full_url,
                verify=self._ssl_verify,
                headers=headers,
                params=endpoint_params,
                data=data,
                timeout=self._request_timeout)
        except requests.exceptions.RequestException as e:
            self._logger.error(msg=(str(e)))
            raise FalconPlayerApiException("Request failed") from e

        # Deserialize JSON response from the request, catch and raise any exceptions
        try:
            data_out = response.json()
        except (ValueError, json.JSONDecodeError) as e:
            self._logger.error(msg=log_line_post.format(False, None, e))
            raise FalconPlayerApiException("Invalid JSON in response") from e

        # If statue_code is in the "OK" range (200 - 299), return the successful result.
        #  Otherwise, catch and raise any exceptions
        is_success = 299 >= response.status_code >= 200  # OK response
        log_line = log_line_post.format(is_success, response.status_code, response.reason)
        if is_success:
            self._logger.debug(msg=log_line)
            return FalconPlayerApiResult(
                response.status_code,
                message=response.reason,
                data=data_out)
        self._logger.error(msg=log_line)
        raise FalconPlayerApiException("{}: {}".format(
            response.status_code, response.reason
        ))

    # GET method for REST Adapter
    #  def get(self, endpoint: str, endpoint_params: Dict = None) -> List[Dict]:
    def get(self, endpoint: str, endpoint_params: Dict = None) -> FalconPlayerApiResult:
        """
        GET request for the REST adapter
        :param endpoint: The endpoint string for the HTTP request (example: system/info)
        :param endpoint_params: (optional) Parameters to pass along with the request
        :return: Response from the API endpoint, cast as a FalconPlayerApiResult object
        """
        return self._do(http_method='GET', endpoint=endpoint, endpoint_params=endpoint_params)

    # POST method for REST Adapter
    #  def post(self, endpoint: str, endpoint_params: Dict = None, data: Dict = None) -> List[Dict]:
    def post(self, endpoint: str, endpoint_params: Dict = None, data: Dict = None) -> FalconPlayerApiResult:
        """
        POST request for the REST adapter
        :param endpoint: The endpoint string for the HTTP request (example: system/info)
        :param endpoint_params: (optional) Parameters to pass along with the request
        :param data: (optional) The data payload for the request
        :return: Response from the API endpoint, cast as a FalconPlayerApiResult object
        """
        return self._do(
            http_method='POST',
            endpoint=endpoint,
            endpoint_params=endpoint_params,
            data=data)

    # DELETE method for REST Adapter
    #  def delete(self, endpoint: str, endpoint_params: Dict = None, data: Dict = None):
    def delete(self, endpoint: str, endpoint_params: Dict = None, data: Dict = None) -> FalconPlayerApiResult:
        """
        DELETE request for the REST adapter
        :param endpoint: The endpoint string for the HTTP request (example: system/info)
        :param endpoint_params: (optional) Parameters to pass along with the request
        :param data: (optional) The data payload for the request
        :return: Response from the API endpoint, cast as a FalconPlayerApiResult object
        :return:
        """
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
        fpp_api = FalconPlayerRestAdapter(hostname=self.ip, timeout=self.timeout, logger=self.logger)
        fpp_api_endpoint = "system/info"

        self.logger.info("Querying for Falcon Player at '{}{}'".format(
            fpp_api.url,
            fpp_api_endpoint))

        fpp_response = fpp_api.get(fpp_api_endpoint)

        # Show response details
        self.logger.info(fpp_response)
        #  self.logger.debug(json.dumps(fpp_response))

        # Set player info
        response = json.dumps(fpp_response.data)
        self.logger.info(response)
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
