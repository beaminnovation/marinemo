# testbed_api_engine.py

class TestbedAPIEngine:
    def __init__(self, config):
        """
        Initialize the API engine with the given configuration.

        Args:
            config (dict): Configuration dictionary containing API endpoints, authentication tokens, etc.
        """
        self.config = config
        self.session = self.create_session()

    def create_session(self):
        """
        Create a session object for making API requests.
        
        Returns:
            requests.Session: Configured session object.
        """
        import requests
        session = requests.Session()
        # Configure session (e.g., headers, authentication)
        session.headers.update({'Authorization': f"Bearer {self.config.get('api_token')}"})
        return session

    def get_status(self):
        """
        Get the status of the testbed.

        Returns:
            dict: Status information of the testbed.
        """
        url = self.config.get('status_endpoint')
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def start_test(self, test_id, params):
        """
        Start a test on the testbed.

        Args:
            test_id (str): Identifier for the test.
            params (dict): Parameters for the test.

        Returns:
            dict: Response from the testbed API.
        """
        url = self.config.get('start_test_endpoint').format(test_id=test_id)
        response = self.session.post(url, json=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def stop_test(self, test_id):
        """
        Stop a test on the testbed.

        Args:
            test_id (str): Identifier for the test.

        Returns:
            dict: Response from the testbed API.
        """
        url = self.config.get('stop_test_endpoint').format(test_id=test_id)
        response = self.session.post(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_results(self, test_id):
        """
        Get the results of a test.

        Args:
            test_id (str): Identifier for the test.

        Returns:
            dict: Test results from the testbed API.
        """
        url = self.config.get('results_endpoint').format(test_id=test_id)
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def create_slice(self, slice_params):
        """
        Create a new network slice on the testbed.

        Args:
            slice_params (dict): Parameters for the network slice.

        Returns:
            dict: Response from the testbed API.
        """
        url = self.config.get('create_slice_endpoint')
        response = self.session.post(url, json=slice_params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def delete_slice(self, slice_id):
        """
        Delete an existing network slice on the testbed.

        Args:
            slice_id (str): Identifier for the network slice.

        Returns:
            dict: Response from the testbed API.
        """
        url = self.config.get('delete_slice_endpoint').format(slice_id=slice_id)
        response = self.session.delete(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

# Example usage
if __name__ == "__main__":
    config = {
        'api_token': 'your_api_token_here',
        'status_endpoint': 'https://example.com/api/status',
        'start_test_endpoint': 'https://example.com/api/tests/{test_id}/start',
        'stop_test_endpoint': 'https://example.com/api/tests/{test_id}/stop',
        'results_endpoint': 'https://example.com/api/tests/{test_id}/results',
        'create_slice_endpoint': 'https://example.com/api/slices',
        'delete_slice_endpoint': 'https://example.com/api/slices/{slice_id}',
    }

    engine = TestbedAPIEngine(config)
    status = engine.get_status()
    print("Status:", status)
