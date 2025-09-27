import json
import logging
import requests
import requests.packages
import urllib3
from typing import List, Dict
from urllib3.fields import format_header_param_html5

# Class for Media Object
class Media:
    Free: int
    Total: int

# Class for Disk Object
class Disk:
    Media: Media
    Root: Media

# Class for Utilization object
class Utilization:
    CPU: float
    Memory: float
    Uptime: str
    Disk: Disk

# Class for System object
class System:
    HostName: str
    HostDescription: str
    Platform: str
    Variant: str
    SubPlatform: str
    backgroundColor: str
    Mode: str
    Logo: str
    Version: str
    Branch: str
    multisync: bool
    OSVersion: str
    OSRelease: str
    channelRanges: str
    majorVersion: int
    minorVersion: int
    typeId: int
    uuid: str
    Utilization: Utilization
    Kernel: str
    LocalGitVersion: str
    RemoteGitVersion: str
    UpgradeSource: str
    IPs: List[str]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return ("IPs: {} | Name: {} | Description: {} | Platform: {} ({}) | Version: {} | Mode: {}".format(
            " , ".join(self.IPs), self.HostName, self.HostDescription, self.Platform, self.Variant, self.Version, self.Mode
        ))

# Class for Falcon Player API endpoints
class FalconPlayerApiEndpoint:
    def __init__(self, path: str = "", description: str = "", params: Dict = None, method: str = "GET"):
        """
        Constructor for a Falcon Player API endpoint
        :param path: The path for the endpoint
        :param description: The description of the endpoint
        :param params: The parameters for the endpoint
        :param method: The HTTP method for the endpoint
        """
        self.path = path
        self.description = description
        self.params = params
        self.method = method

    def __str__(self):
        return 'Path: {} | Description: {} | Method: {}'.format(
            self.path, self.description, self.method)


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
            self.endpoints[endpoint.path] = endpoint

            return

        def get_endpoint(endpoint_path: str = ""):
            try:
                return self.endpoints[endpoint_path]
            except Exception as e:
                raise FalconPlayerApiException("Error retrieving endpoint") from e


# Class for responses from the Falcon Player API
class FalconPlayerApiResult:
    def __init__(self, status_code: int, message: str = '', data: List[Dict] = None):
        """
        Constructor for a Falcon Player API result. Wraps elements of a request.response object
        :param status_code: The status code of the response
        :param message: The message of the response
        :param data: The data returned from the response
        """
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
    def __init__(self, ip: str, system: System, timeout: int = None, logger: logging.Logger = None) -> None:
        """
        Constructor for the FalconPlayer class
        :param ip: IP address or hostname of the Falcon Player
        :param system: System object for the details of the Falcon Player
        :param timeout: (optional) Timeout, in seconds, for the request
        :param logger: (optional) Pass an existing logger to the constructor
        """
        self.ip = ip
        self.system = system
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def connect(ip: str, timeout: int = None, logger: logging.Logger = None):
        """
        Static method to create a new FalconPlayer instance
        :param ip: IP address or hostname of the Falcon Player
        :param timeout: (optional) Timeout, in seconds, for the request
        :param logger: (optional) Pass an existing logger to the constructor
        :return: FalconPlayer instance
        """
        fpp_api = FalconPlayerRestAdapter(hostname=ip, timeout=timeout, logger=logger)
        fpp_api_endpoint = "system/info"

        logger.debug("Querying for Falcon Player at '{}{}'".format(
            fpp_api.url,
            fpp_api_endpoint))

        fpp_response = fpp_api.get(fpp_api_endpoint)

        return FalconPlayer(ip=ip, system=System(**fpp_response.data), timeout=timeout, logger=logger)

    def get_endpoints(self, endpoint_filter: str = ""):
        """
        Method to get all endpoints for the Falcon Player API
        :param endpoint_filter: String to filter endpoints on. Defaults to empty string.
        :return: List of endpoints
        """
        fpp_api_query = FalconPlayerRestAdapter(hostname=self.ip, timeout=self.timeout, logger=self.logger)
        fpp_api_endpoint = "endpoints.json"

        fpp_response = fpp_api_query.get(fpp_api_endpoint)

        endpoints = []

        for endpoint in fpp_response.data["endpoints"]:
            endpoint_path = endpoint["endpoint"]

            if str(endpoint_path).find(endpoint_filter) >= 0:
                self.logger.debug("Endpoint Path: {}".format(endpoint_path))

                endpoint_method_keys = endpoint["methods"].keys()
                self.logger.debug("Methods for {}: {}".format(endpoint_path, endpoint_method_keys))

                for method_key in endpoint_method_keys:
                    endpoint_desc = endpoint["methods"][method_key]["desc"]

                    new_endpoint = FalconPlayerApiEndpoint(
                        path=endpoint_path,
                        description=endpoint_desc,
                        method=method_key)

                    endpoints.append(new_endpoint)

                    self.logger.debug("Endpoint added: {}".format(new_endpoint))

        return endpoints

    def get_endpoint_detail(self, endpoint_path):
        """
        Method to get details for endpoints in the Falcon Player API that match the given path
        :param endpoint_path: The endpoint path
        :return: FalconPlayerApiEndpoint object
        """
        self.logger.debug("Getting details for endpoint: {}".format(endpoint_path))

        # Get endpoints that match the search filter
        endpoints = self.get_endpoints(endpoint_filter=endpoint_path)

        matching_endpoints = [endpoint for endpoint in endpoints if endpoint.path == endpoint_path]

        return matching_endpoints if len(matching_endpoints) > 0 else None

    def run_endpoint(self, endpoint_path: str, endpoint_params: dict = None, endpoint_data: dict = None,
                     endpoint_method: str = "GET"):
        fpp_api_adapter = FalconPlayerRestAdapter(hostname=self.ip, timeout=self.timeout)

        self.logger.info("Endpoint: {} | Method: {} | Params: {}".format(
            endpoint_path, endpoint_method, endpoint_params))

        if endpoint_method == "GET":
            fpp_response = fpp_api_adapter.get(endpoint_path, endpoint_params)
        elif endpoint_method == "POST":
            fpp_response = fpp_api_adapter.post(endpoint_path, endpoint_params, endpoint_data)
        elif endpoint_method == "DELETE":
            fpp_response = fpp_api_adapter.delete(endpoint_path, endpoint_params, endpoint_data)
        else:
            raise FalconPlayerApiException("Invalid JSON in response")

        return fpp_response

    def __str__(self):
        return "{}".format(self.system)
