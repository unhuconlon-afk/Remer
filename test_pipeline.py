import unittest
import json
from unittest.mock import patch, MagicMock

# ── Import target project modules ────────────────────────────────────────────
from ollama_analyzer import analyze_text_with_ollama
from calendar_syncer import insert_event_to_google

class TestProjectPipeline(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_ollama_analysis_success(self, mock_urlopen):
        """Test successful local Ollama API communication with mocked response."""
        # Mocking the HTTP response from Ollama API
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": json.dumps({
                "co_lich_hen": True,
                "loai_thong_bao": "lich_hen",
                "intent": "Meeting",
                "summary": "Mai 9h họp",
                "datetime": "2026-06-04T09:00:00+07:00",
                "duration_minutes": 60,
                "participants": []
            })
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = analyze_text_with_ollama("Mai 9h họp")
        self.assertEqual(res["intent"], "Meeting")
        self.assertEqual(res["summary"], "Mai 9h họp")
        self.assertEqual(res["datetime"], "2026-06-04T09:00:00+07:00")

    @patch('calendar_syncer.get_calendar_service')
    def test_calendar_sync(self, mock_get_service):
        """Test calendar event construction and API insertion mapping."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock insert execution return value
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {"htmlLink": "https://calendar.google.com/event?id=test"}
        mock_service.events.return_value.insert.return_value = mock_insert

        event_data = {
            "intent": "Meeting",
            "summary": "Test Meeting Sync",
            "datetime": "2026-06-04T09:00:00+07:00",
            "duration_minutes": 60,
            "participants": []
        }

        res = insert_event_to_google(event_data)
        self.assertEqual(res.get("htmlLink"), "https://calendar.google.com/event?id=test")
        
        # Verify correct args passed to Google Calendar API insert function
        mock_service.events.return_value.insert.assert_called_once()
        called_args = mock_service.events.return_value.insert.call_args[1]
        self.assertEqual(called_args["calendarId"], "primary")
        self.assertEqual(called_args["body"]["summary"], "Test Meeting Sync")
        self.assertEqual(called_args["body"]["start"]["dateTime"], "2026-06-04T09:00:00+07:00")

if __name__ == '__main__':
    unittest.main()
