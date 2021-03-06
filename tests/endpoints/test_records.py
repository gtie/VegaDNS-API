import json

from mock import MagicMock

import vegadns.api.endpoints.records
import vegadns.api.models.record
import vegadns.api.models.domain
from vegadns.api import app
from tests.endpoints import AbstractEndpointTest


class TestRecords(AbstractEndpointTest):
    def test_get_success(self):
        record_one = vegadns.api.models.record.Record()

        record_one.distance = 0
        record_one.domain_id = 1
        record_one.host = "1.b.vegadns.ubuntu"
        record_one.port = None
        record_one.record_id = 8
        record_one.ttl = 3600
        record_one.type = "A"
        record_one.val = "1.2.3.4"
        record_one.weight = None

        record_two = vegadns.api.models.record.Record()

        record_two.distance = 0
        record_two.domain_id = 1
        record_two.host = "hostmaster.test3.com:ns1.vegadns.ubuntu"
        record_two.port = None
        record_two.record_id = 9
        record_two.ttl = 86400
        record_two.type = "S"
        record_two.val = "16384:2048:1048576:2560"
        record_two.weight = None

        vegadns.api.models.domain.Domain.get_records = MagicMock(
            return_value=[record_one, record_two]
        )
        vegadns.api.models.domain.Domain.count_records = MagicMock(
            return_value=2
        )
        domain = vegadns.api.models.domain.Domain()

        vegadns.api.endpoints.records.Records.get_domain = MagicMock(
            return_value=domain
        )
        vegadns.api.endpoints.records.Records.get_read_domain = MagicMock(
            return_value=domain
        )

        self.mock_auth('test@test.com', 'test')

        response = self.open_with_basic_auth(
            '/records?domain_id=1',
            'GET',
            'test@test.com',
            'test'
        )
        self.assertEqual(response.status, "200 OK")

        decoded = json.loads(response.data)
        self.assertEqual(decoded['status'], "ok")
        self.assertEqual(decoded['total_records'], 2)
        self.assertEqual(decoded['records'][0]['record_id'], 8)
        self.assertEqual(decoded['records'][0]['record_type'], 'A')
        self.assertEqual(decoded['records'][1]['record_id'], 9)
        self.assertEqual(decoded['records'][1]['record_type'], 'SOA')
