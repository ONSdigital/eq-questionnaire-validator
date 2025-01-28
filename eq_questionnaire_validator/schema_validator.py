import glob
import json
import logging
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Validator:
    def __init__(
        self, checks: int, max_workers: int,
    ):
        self.checks = checks
        self.max_workers = max_workers
        self.error = False
        self.passed = 0
        self.failed = 0

    def check_connection(self):
        checks = self.checks

        while checks > 0:
            response = subprocess.run(
                [
                    "curl",
                    "-so",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    "http://localhost:5002/status",
                ],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()

            if response != "200":
                logging.error("\033[31m---Error: Schema Validator Not Reachable---\033[0m")
                logging.error(f"\033[31mHTTP Status: {response}\033[0m")
                if checks != 1:
                    logging.info("Retrying...\n")
                    time.sleep(5)
                else:
                    logging.info("Exiting...\n")
                    return False
                checks -= 1
            else:
                checks = 0

        return True

    def validate(self):

        if len(sys.argv) == 1 or sys.argv[1] == "--local":
            file_path = "./schemas"

        else:
            file_path = sys.argv[1]

        schemas = glob.glob(os.path.join(file_path, "**", "*.json"), recursive=True)
        logging.info(f"--- Testing Schemas in {file_path} ---")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_schema = {
                executor.submit(self.validate_schema, schema): schema for schema in schemas
            }
            for future in as_completed(future_to_schema):
                schema = future_to_schema[future]
                try:
                    schema_path, result = future.result()
                    # Extract HTTP body
                    http_body = re.sub(r"HTTPSTATUS:.*", "", result)

                    # Convert HTTP body to JSON
                    http_body_json = json.loads(http_body)

                    # Format JSON
                    formatted_json = json.dumps(http_body_json, indent=4)

                    # Extract HTTP status code
                    result_response = re.search(r"HTTPSTATUS:(\d+)", result)[1]

                    if result_response == "200" and http_body_json == {}:
                        logging.info(f"\033[32m{schema_path}: PASSED\033[0m")
                        self.passed += 1
                    else:
                        logging.error(f"\033[31m{schema_path}: FAILED\033[0m")
                        logging.error(
                            f"\033[31mHTTP Status @ /validate: {result_response}\033[0m"
                        )
                        logging.error(f"\033[31mHTTP Status: {formatted_json}\033[0m")
                        self.error = True
                        self.failed += 1
                except Exception as e:
                    logging.error(f"\033[31mError processing {schema}: {e}\033[0m")

        logging.info(f"\033[32m{self.passed} passed\033[0m - \033[31m{self.failed} failed\033[0m")
        if self.error:
            sys.exit(1)

    def validate_schema(self, schema_path):
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-w",
                    "HTTPSTATUS:%{http_code}",
                    "-X",
                    "POST",
                    "-H",
                    "Content-Type: application/json",
                    "-d",
                    f"@{schema_path}",
                    "http://localhost:5001/validate",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return schema_path, result.stdout
        except subprocess.CalledProcessError as e:
            logging.info(f"Error validating schema {schema_path}: {e}")
            return schema_path, None