from ivycheck.ivy_client import IvyClient
from typing import Optional, Dict


class Evaluator:
    def __init__(self, client, test_dataset_id: str, segments: Optional[Dict] = None):
        self.client = client
        self.test_dataset_id = test_dataset_id
        self.segments = segments
        self.evaluation_dataset_id = None
        self.test_cases = None
        self._prepare_evaluation_dataset()

    @classmethod
    def create(
        cls, client: IvyClient, test_dataset_id: str, segments: Optional[Dict] = None
    ):
        return cls(client, test_dataset_id, segments)

    def _prepare_evaluation_dataset(self):
        # Reads the test dataset and creates the evaluation dataset
        test_dataset = self.client.TestDataset.read(
            testcasedataset_id=self.test_dataset_id
        )
        evals = self.client.EvaluationDataset.create(
            test_case_dataset_id=self.test_dataset_id,
            description="Automated Evaluation",
        )
        self.evaluation_dataset_id = evals["id"]
        # Filter test_cases if segments is provided
        if self.segments:
            self.test_cases = [
                tc
                for tc in test_dataset["test_cases"]
                if self._test_case_matches_segments(tc)
            ]
        else:
            self.test_cases = test_dataset["test_cases"]

    def _test_case_matches_segments(self, test_case):
        # Implement the logic to check if a test case matches the segments filter
        for key, value in self.segments.items():
            if test_case["segments"].get(key) != value:
                return False
        return True

    def test_case_iterator(self):
        # Iterator for test cases that yields a tuple containing the test case data and a method to evaluate it
        for test_case in self.test_cases:
            yield (test_case, self._make_evaluate_func(test_case["id"]))

    def _make_evaluate_func(self, test_case_id):
        # Create function that captures the test case ID and takes a response as its only argument
        def evaluate_func(response: str):
            self.client.Evaluation.create_and_run(
                evaluation_dataset_id=self.evaluation_dataset_id,
                test_case_id=test_case_id,
                output={"response": response},
            )

        return evaluate_func