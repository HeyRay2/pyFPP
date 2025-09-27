# Import libraries
from tokenize import endpats

from fpp_classes import FalconPlayer, FalconPlayerRestAdapter, System
import argparse  # argument parsing
import asyncio
import re  # regex
import logging  # Logging
from pathlib import Path  # Path functions

# Set a default command response timeout (in seconds)
command_timeout_default = 3

# List of valid device command options
#  command_options = ['stop-playlist', 'start-playlist', 'reset', 'info']
command_options = ['endpoint-list', 'endpoint-detail', 'endpoint-run']

# CMD Line Parser
parser = argparse.ArgumentParser(description='Send Commands to Falcon Pi Player (FPP).')
parser.add_argument('--ip', help='The IP address of the FPP', required=True)
parser.add_argument('--command', help='Command to run', choices=command_options, required=True)
parser.add_argument('--command_params', help='Params to pass for the command')
parser.add_argument('--endpoint_name', help='Used in conjunction with the "endpoint-list" command. '
                                            'Filters the endpoint list for those matching the entered value')
parser.add_argument('--endpoint_params', help='Used in conjunction with the "endpoint-run" command. '
                                            'Passes parameters to the endpoint')
parser.add_argument('--endpoint_data', help='Used in conjunction with the "endpoint-run" command. '
                                            'Passes data to the endpoint')
parser.add_argument('--endpoint_method', help='HTTP method to use for the endpoint-run command',
                    default='GET', choices=['GET', 'POST', 'DELETE'])
parser.add_argument('--timeout', type=int,
                    help='Timeout for command (in seconds)', default=command_timeout_default)
parser.add_argument('--log', help='File path for log file. Defaults to script folder if omitted')
parser.add_argument('--debug', type=bool, help='Verbose mode for debugging', nargs='?', const=True)

# Get CMD Args
args = parser.parse_args()
logLevel = logging.DEBUG if args.debug else logging.INFO

# Initialize logger (so functions can utilize it)
loggerName = "myLogger"
logPath = args.log if args.log else "."
logger = logging.getLogger(loggerName)


# Functions
def run_command(player_ip, command, command_params, command_timeout):
    # Access the Player
    player = FalconPlayer.connect(player_ip, command_timeout, logger)

    # Show Falcon Player system details
    logger.info(player)

    # Run command on target Falcon Player
    logger.info('Command: {}'.format(command))

    # Perform command action
    if command == "endpoint-list":
        endpoint_list_filter = args.endpoint_name
        logger.info('Endpoint Name Filter: {}'.format(endpoint_list_filter if endpoint_list_filter else "None"))
        endpoints = player.get_endpoints(endpoint_list_filter if endpoint_list_filter else "")

        logger.info("=====================")
        logger.info("Endpoints Found: {}".format(len(endpoints)))
        logger.info("=====================")

        for endpoint in endpoints:
            logger.info(endpoint)
    elif command == "endpoint-detail":
        endpoint_name = args.endpoint_name
        if endpoint_name:
            endpoints = player.get_endpoint_detail(endpoint_name)

            if endpoints:
                logger.info("=====================")
                logger.info("Endpoints Found: {}".format(len(endpoints)))
                logger.info("=====================")

                for endpoint in endpoints:
                    logger.info(endpoint)
                    logger.info("Params: {}".format(endpoint.params))
            else:
                logger.error("No endpoint match found for '{}'".format(endpoint_name))
        else:
            logger.error("No endpoint path provided!")
    elif command == "endpoint-run":
        endpoint_run_result = player.run_endpoint(args.endpoint_name, args.endpoint_params,
                                                  args.endpoint_data, args.endpoint_method)

        logger.info("Endpoint run status: {} - {}".format(
            endpoint_run_result.status_code, endpoint_run_result.message))
        logger.info("Endpoint run result: {}".format(endpoint_run_result.data))
        # logger.info('Running endpoint query not yet implemented')
    else:
        logger.critical('Unknown or unsupported command: {}'.format(command))


def config_logger(log_name_prefix, log_level, log_path):
    # Log path existence / creation
    Path(log_path).mkdir(parents=True, exist_ok=True)

    # Log filename
    log_file_name = '{}/{}.log'.format(log_path, log_name_prefix)

    # Get logger
    my_logger = logging.getLogger(loggerName)

    # Set lowest allowed logger severity
    logger.setLevel(logging.DEBUG)

    # Console output handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
    logger.addHandler(console_handler)

    # Log file output handler
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setLevel(log_level)
    file_handler.encoding = 'utf-8'
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)d: %(message)s'))
    logger.addHandler(file_handler)

    # Return configured logger
    return my_logger


# Main function
async def main():
    # Configure logging
    logger = config_logger(Path(parser.prog).stem, logLevel, logPath)

    # Get command timeout
    command_timeout = args.timeout

    # Check for valid IP address
    if re.match(
            r"(?:\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b)\Z",
            args.ip):

        # Successful match at the start of the string
        player_ip = args.ip
    else:
        # IP match attempt failed
        logger.critical('Invalid IP Address: {}'.format(args.ip))
        exit()

    #  Get command from CMD args
    command = args.command

    # Check for valid command
    if command in command_options:
        # Try to run command
        try:
            command_params = args.command_params
            run_command(player_ip, command, command_params, command_timeout)
        except Exception as e:
            logger.critical('Error: {}'.format(e))
    else:
        logger.critical('Invalid command: {}'.format(command))
        exit()


# Initiate main
if __name__ == "__main__":
    asyncio.run(main())
else:
    help()
