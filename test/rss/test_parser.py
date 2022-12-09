import unittest
from unittest.mock import patch

from atoma import FeedDocumentError
from requests import ConnectTimeout

from src.rss import parser
from test.rss import fixtures


class TestRssParser(unittest.TestCase):
    @patch('src.rss.parser.requests.get')
    def test_parser_animetosho(self, mock_requests_get):
        # Arrange
        feed_link = 'https://feed.animetosho.org/rss2?only_tor=1'
        log = []

        # Configure the mock parser() function to return our mock response
        mock_requests_get.return_value = fixtures.animetosho_response

        # Act
        result = parser(feed_link, log)

        # Assert
        self.assertEqual(result, {
            '[NC-Raws] 秋叶原女仆战争 / Akiba Maid Sensou - 10 (Sentai 1920x1080 AVC AAC MKV)': [
                'magnet:?xt=urn:btih:THNJLNPHYBXWEFCTUINLMOOGQ2SQ6HDE&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce'
                '&tr=http%3A%2F%2Ftr.bangumi.moe%3A6969%2Fannounce&tr=http%3A%2F%2Ft.acg.rip%3A6699%2Fannounce'
                '&tr=http%3A%2F%2Fopentracker.acgnx.se%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce'
                '&dn=%5BNC-Raws%5D%20%E7%A7%8B%E5%8F%B6%E5%8E%9F%E5%A5%B3%E4%BB%86%E6%88%98%E4%BA%89%20%2F%20Akiba'
                '%20Maid%20Sensou%20-%2010%20%28Sentai%201920x1080%20AVC%20AAC%20MKV%29',
                'https://animetosho.org/storage/torrent/99da95b5e7c06f621453a21ab639c686a50f1c64/%5BNC-Raws%5D%20Akiba'
                '%20Maid%20Sensou%20-%2010%20%28Sentai%201920x1080%20AVC%20AAC%20MKV%29%20%5B26D00225%5D.torrent'
            ]
        })

    @patch('src.rss.parser.requests.get')
    def test_parser_nyaa_si(self, mock_requests_get):
        # Arrange
        feed_link = 'https://nyaa.si/?page=rss'
        log = []

        # Configure the mock parser() function to return our mock response
        mock_requests_get.return_value = fixtures.nyaa_si_response

        # Act
        result = parser(feed_link, log)

        # Assert
        self.assertEqual(result, {
            '[Yameii] Dungeon ni Deai o Motomeru no wa Machigatte Iru Darouka - Familia Myth IV (DanMachi S4) - 11 '
            '| Is It Wrong to Try to Pick Up Girls in a Dungeon IV [English Dub] [HIDIVE WEB-DL 1080p] [C1302ADC]': [
                None,
                'https://nyaa.si/download/1611493.torrent'
            ]
        })

    @patch('src.rss.parser.requests.get')
    def test_requests_handler(self, mock_requests_get):
        # Arrange
        feed_link = 'https://www.example.com/rss'
        log = []

        # Configure the mock parser() function to return our mock response
        mock_requests_get.side_effect = ConnectTimeout("Mock request get failed")

        # Act
        result = parser(feed_link, log)

        # Assert
        self.assertEqual(result, {})

    @patch('src.rss.parser.requests.get')
    @patch('src.rss.parser.atoma.parse_rss_bytes')
    def test_atoma_parser(self, mock_parser, mock_requests_get):
        # Arrange
        feed_link = 'https://nyaa.si/?page=rss'
        log = []

        # Configure the mock parser() function to return our mock response
        mock_requests_get.return_value = fixtures.nyaa_si_response
        mock_parser.side_effect = FeedDocumentError("Mock exception")

        # Act
        result = parser(feed_link, log)

        # Act
        result = parser(feed_link, log)

        # Assert
        self.assertEqual(result, {})
