import json
import requests

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
        request_url = 'http://{}/api/system/info'.format(self.ip)

        self.logger.info("Querying for controller at '{}'".format(self.ip))

        # Payload
        payload = {}

        # Headers
        headers = {}

        self.logger.debug("Headers: {}".format(headers))

        # Send the request and record the response
        response = requests.request(
            "GET", request_url, headers=headers, data=payload, timeout=self.timeout)

        # response JSON
        response_json = response.json()

        # Verify a valid response was received
        if not response.ok:
            raise Exception("Error accessing Falcon Player at '{}': {} - {}".format(
                self.ip,
                response_json.get("translationKey"),
                response_json.get("error"))
            )

        # Show response details
        self.logger.debug(json.dumps(response.json()))

        # Set player info
        self.hostname = response_json.get("HostName")
        self.description = response_json.get("HostDescription")
        self.platform = response_json.get("Platform")
        self.variant = response_json.get("Variant")
        self.version = response_json.get("Version")
        self.branch = response_json.get("Branch")
        self.mode = response_json.get("Mode")

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