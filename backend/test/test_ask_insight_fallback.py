import unittest

from utils.anthropic_client import ask_claude


class AskClaudeFallbackTests(unittest.TestCase):
    def test_falls_back_to_local_response_when_api_key_is_missing(self):
        answer, error = ask_claude(
            system_prompt="Dataset context placeholder",
            messages=[{"role": "user", "content": "What are the top revenue trends?"}],
            api_key="",
            model="claude-sonnet-5",
            max_tokens=256,
            api_url="https://api.anthropic.com/v1/messages",
        )

        self.assertIsNone(error)
        self.assertTrue(answer)
        self.assertIn("offline", answer.lower())


if __name__ == "__main__":
    unittest.main()
