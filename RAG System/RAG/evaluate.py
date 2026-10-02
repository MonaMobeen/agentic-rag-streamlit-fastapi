import os

from rag_engine import RAGService


class FakeUpload:
    def __init__(self, path):
        self.name = os.path.basename(path)
        with open(path, "rb") as f:
            self._data = f.read()

    def getvalue(self):
        return self._data


PDF_PATH = os.path.join(
    os.path.dirname(__file__), "..",
    "Government_AI_Cloud_High_Level_Architecture_InvoZone.pdf",
)

TEST_CASES = [
    {
        "question": "What is the multi-tenancy principle?",
        "expected_keywords": ["data", "isolat"],
    },
    {
        "question": "What is the capital of France?",
        "expected_keywords": ["couldn't find", "don't"],
    },
    {
        "question": "What does the RAG authorization control?",
        "expected_keywords": ["source", "acl", "author"],
    },
]


def run_evaluation():
    service = RAGService()
    info = service.build_index([FakeUpload(PDF_PATH)])
    print("Index ready:", info)

    passed = 0
    for i, case in enumerate(TEST_CASES, start=1):
        answer, sources = service.ask_with_agent(case["question"])
        answer_lower = answer.lower()

        found = any(kw.lower() in answer_lower for kw in case["expected_keywords"])

        print(f"\nTest {i}: {case['question']}")
        print("Answer:", answer[:200])
        print("Result:", "PASS" if found else "FAIL")

        if found:
            passed += 1

    total = len(TEST_CASES)
    print(f"\n--- Score: {passed}/{total} ({passed/total*100:.0f}%) ---")


if __name__ == "__main__":
    run_evaluation()