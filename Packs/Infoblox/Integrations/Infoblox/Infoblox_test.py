from Infoblox import Client
import demistomock as demisto
import json
import pytest
from CommonServerPython import DemistoException

BASE_URL = 'https://example.com/v1/'
client = Client('https://example.com/v1/', params={'_return_as_object': '1'})


class TestHelperFunctions:
    # disable-secrets-detection-start
    SSL_ERROR = "Failed to parse json object from response: b'<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" " \
                "content=\"text/html; charset=utf-8\">\r\n<META HTTP-EQUIV=\"PRAGMA\" CONTENT=\"NO-CACHE\">\r\n<meta " \
                "name=\"viewport\" content=\"initial-scale=1.0\">\r\n<title>Certificate Error</title>\r\n<style>\r\n  " \
                "#content {\r\n    border:3px solid#aaa;\r\n    background-color:#fff;\r\n    margin:1.5em;\r\n    " \
                "padding:1.5em;\r\n    font-family:Tahoma,Helvetica,Arial,sans-" \
                "serif;\r\n    font-size:1em;\r\n  }\r\n  " \
                "h1 {\r\n    font-size:1.3em;\r\n    font-weight:bold;\r\n    color:#196390;\r\n  }\r\n  b {\r\n    " \
                "color:#196390;\r\n  }\r\n</style>\r\n</head>\r\n<body " \
                "\">\r\n<div id=\"content\">\r\n<h1>Certificate Error</h1>\r\n<p>There is an issue with " \
                "the SSL certificate of the server you are trying to contact.</p>\r\n<p><b>Certificate Name:</b> " \
                "www.infoblox.com </p>\r\n<p><b>IP:</b> </p>\r\n<p><b>Category:</b> any </p>\r\n<p><b>Issuer:</b> " \
                "www.infoblox.com </p>\r\n<p><b>Status:</b> expired </p>\r\n<p><b>Reason:</b>  </p>\r\n<p><b>User:" \
                "</b> </p>\r\n</div>\r\n</body>\r\n</html>\r\n\r\n'"
    #  disable-secrets-detection-end

    API_ERROR_OBJ = {
        "Error": "AdmConDataError: None (IBDataConflictError: IB.Data.Conflict:Duplicate object 'test123.com' of type "
                 "zone "
                 "exists in the database.)",
        "code": "Client.Ibap.Data.Conflict",
        "text": "Duplicate object 'test123.com' of type zone exists in the database."
    }

    def test_parse_demisto_exception_unauthorized_error(self):
        from Infoblox import parse_demisto_exception
        json_err = 'Expecting value: line 1 column 1 (char 0)'
        api_err = 'Error in API call [401] - Authorization Required'
        parsed_err = parse_demisto_exception(DemistoException(api_err, json_err))
        assert str(parsed_err) == str(
            DemistoException("Authorization error, check your credentials."))

    def test_parse_demisto_exception_json_parse_error(self):
        from Infoblox import parse_demisto_exception
        json_err = 'Expecting value: line 1 column 1 (char 0)'
        api_err = f'Failed to parse json object from response: {self.SSL_ERROR}'
        parsed_err = parse_demisto_exception(DemistoException(api_err, json_err))
        assert str(parsed_err) == str(
            DemistoException("Cannot connect to Infoblox server, check your proxy and connection."))

    def test_parse_demisto_exception_api_error(self):
        from Infoblox import parse_demisto_exception
        api_err = f'Error in API call [400] - Bad Request\n {json.dumps(self.__class__.API_ERROR_OBJ)}'
        parsed_err = parse_demisto_exception(DemistoException(api_err))
        assert str(parsed_err) == str(
            DemistoException("Duplicate object 'test123.com' of type zone exists in the database."))


class TestZonesOperations:
    POST_NEW_ZONE_RESPONSE = {
        "result": {
            "_ref": "zone_rp/ZG5zLnpvbmUkLl9kZWZhdWx0LmNvbS50ZXN0:test.com/default",
            "disable": False,
            "fqdn": "test.com",
            "rpz_policy": "GIVEN",
            "rpz_severity": "WARNING",
            "rpz_type": "LOCAL",
            "view": "default"
        }
    }
    REQUEST_PARAM_ZONE = '?_return_as_object=1&_return_fields%2B=fqdn%2Crpz_policy%2Crpz_severity%2Crpz_type%2C' \
                         'substitute_name%2Ccomment%2Cdisable'

    def test_create_response_policy_zone_command(self, mocker, requests_mock):
        from Infoblox import create_response_policy_zone_command
        mocker.patch.object(demisto, 'params', return_value={})
        requests_mock.post(f'{BASE_URL}zone_rp{self.__class__.REQUEST_PARAM_ZONE}',
                           json=self.__class__.POST_NEW_ZONE_RESPONSE)
        human_readable, context, raw_response = create_response_policy_zone_command(
            client, self.__class__.POST_NEW_ZONE_RESPONSE.get("result"))
        assert human_readable == "### Infoblox Integration - Response Policy Zone: test.com has been created\n" \
                                 "|Disable|FQDN|Reference ID|Rpz Policy|Rpz Severity|Rpz Type|View|\n" \
                                 "|---|---|---|---|---|---|---|\n" \
                                 "| false | test.com | zone_rp/ZG5zLnpvbmUkLl9kZWZhdWx0LmNvbS50ZXN0:test.com/default " \
                                 "| GIVEN | WARNING | LOCAL | default |\n"
        assert context == {
            'Infoblox.ResponsePolicyZones(val.FQDN && val.FQDN === obj.FQDN)': [{
                'ReferenceID': 'zone_rp/ZG5zLnpvbmUkLl9kZWZhdWx0LmNvbS50ZXN0:test.com/default',
                'Disable': False,
                'FQDN': 'test.com',
                'RpzPolicy': 'GIVEN',
                'RpzSeverity': 'WARNING',
                'RpzType': 'LOCAL',
                'View': 'default'
            }]
        }
        assert raw_response == {
            'result': {
                '_ref': 'zone_rp/ZG5zLnpvbmUkLl9kZWZhdWx0LmNvbS50ZXN0:test.com/default',
                'disable': False,
                'fqdn': 'test.com',
                'rpz_policy': 'GIVEN',
                'rpz_severity': 'WARNING',
                'rpz_type': 'LOCAL',
                'view': 'default'
            }}


class TestRecordsOperations:
    """
    A General Test class for infoblox API functions, using pytest mocker.
    """
    from Infoblox import list_records_command, list_hosts_command, search_host_record_command, \
        create_a_record_command, add_host_record_command, update_host_ip_command, update_a_record_command

    TEST_LIST_RECORDS_DATA = {
        "args": {"zone": "foo.com"},
        "human_readable": ("### Infoblox Integration - List of All Records: \n"
                           "|Comment|Name|Reference ID|Type|View|Zone|\n"
                           "|---|---|---|---|---|---|\n"
                           "| Auto-created by Add Zone |  | allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JC4uZmFrZV9iaW5kX25z"
                           "JC5zcmdfcm9vdC4zLi5uaW9zLnBvYy5pbmZvYmxveC5sb2NhbHwuX2RlZmF1bHQuY29tLmZvb3x8bmlvcy5wb2MuaW5"
                           "mb2Jsb3gubG9jYWw: | UNSUPPORTED | default | foo.com |\n"
                           "| Auto-created by Add Zone |  | allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5iaW5kX3NvYSQu"
                           "X2RlZmF1bHQuY29tLmZvbw: | UNSUPPORTED | default | foo.com |\n"
                           "|  |  | allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLg: | "
                           "record:host_ipv4addr | default | foo.com |\n"
                           "|  | kaka | allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLm"
                           "tha2E:kaka | record:host_ipv4addr | default | foo.com |\n"
                           "|  | pointer | allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9v"
                           "Lmtha2E:pointer | UNSUPPORTED | default | foo.com |\n"
                           "|  | remote | allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLm"
                           "tha2E:remote | UNSUPPORTED | default | foo.com |\n"),
        "context": {
            "Infoblox.Record(val.ReferenceID && val.ReferenceID === obj.ReferenceID)": [
                {
                    "ReferenceID": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JC4uZmFrZV9iaW5kX25zJC5zcmdfcm9vdC4zLi5uaW9"
                                   "zLnBvYy5pbmZvYmxveC5sb2NhbHwuX2RlZmF1bHQuY29tLmZvb3x8bmlvcy5wb2MuaW5mb2Jsb3gubG9jYWw:",
                    "Comment": "Auto-created by Add Zone",
                    "Name": "",
                    "Type": "UNSUPPORTED",
                    "View": "default",
                    "Zone": "foo.com"
                },
                {
                    "ReferenceID": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5iaW5kX3NvYSQuX2RlZmF1bHQuY29tLmZvbw:",
                    "Comment": "Auto-created by Add Zone",
                    "Name": "",
                    "Type": "UNSUPPORTED",
                    "View": "default",
                    "Zone": "foo.com"
                },
                {
                    "ReferenceID": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLg:",
                    "Comment": "",
                    "Name": "",
                    "Type": "record:host_ipv4addr",
                    "View": "default",
                    "Zone": "foo.com"
                },
                {
                    "ReferenceID": "allrecords"
                                   "/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLmtha2E:kaka",
                    "Comment": "",
                    "Name": "kaka",
                    "Type": "record:host_ipv4addr",
                    "View": "default",
                    "Zone": "foo.com"
                },
                {
                    "ReferenceID": "allrecords"
                                   "/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLmtha2E:pointer",
                    "Comment": "",
                    "Name": "pointer",
                    "Type": "UNSUPPORTED",
                    "View": "default",
                    "Zone": "foo.com"
                },
                {
                    "ReferenceID": "allrecords"
                                   "/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLmtha2E:remote",
                    "Comment": "",
                    "Name": "remote",
                    "Type": "UNSUPPORTED",
                    "View": "default",
                    "Zone": "foo.com"
                }
            ]
        },
        "raw_response": {"result": [
            {
                "_ref": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JC4uZmFrZV9iaW5kX25zJC5zcmdfcm9vdC4zLi5uaW9zLnBvYy5pbm"
                        "ZvYmxveC5sb2NhbHwuX2RlZmF1bHQuY29tLmZvb3x8bmlvcy5wb2MuaW5mb2Jsb3gubG9jYWw:",
                "comment": "Auto-created by Add Zone",
                "name": "",
                "type": "UNSUPPORTED",
                "view": "default",
                "zone": "foo.com"
            },
            {
                "_ref": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5iaW5kX3NvYSQuX2RlZmF1bHQuY29tLmZvbw:",
                "comment": "Auto-created by Add Zone",
                "name": "",
                "type": "UNSUPPORTED",
                "view": "default",
                "zone": "foo.com"
            },
            {
                "_ref": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLg:",
                "comment": "",
                "name": "",
                "type": "record:host_ipv4addr",
                "view": "default",
                "zone": "foo.com"
            },
            {
                "_ref": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLmtha2E:kaka",
                "comment": "",
                "name": "kaka",
                "type": "record:host_ipv4addr",
                "view": "default",
                "zone": "foo.com"
            },
            {
                "_ref": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLmtha2E:pointer",
                "comment": "",
                "name": "pointer",
                "type": "UNSUPPORTED",
                "view": "default",
                "zone": "foo.com"
            },
            {
                "_ref": "allrecords/ZG5zLnpvbmVfc2VhcmNoX2luZGV4JGRucy5ob3N0JC5fZGVmYXVsdC5jb20uZm9vLmtha2E:remote",
                "comment": "",
                "name": "remote",
                "type": "UNSUPPORTED",
                "view": "default",
                "zone": "foo.com"
            }
        ]}
    }
    TEST_LIST_HOSTS_DATA = {
        "args": {},
        "human_readable": ("### Infoblox Integration - List of Host Records: \n"
                           "|Ipv 4 Addrs|Reference ID|\n"
                           "|---|---|\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmMuMTczLjE4Lj"
                           "AuNS4:xxx.xxx.xxx.xxx/xtndspf1d8n2c.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'xtndspf1d8n2c.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJj:"
                           "xtndspf1d8n2c.poc.infoblox.local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmQuMTczLjE4L"
                           "jAuMTAu:xxx.xxx.xxx.xxx/xtndspf1d8n2d.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'xtndspf1d8n2d.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | record:"
                           "host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJk:"
                           "xtndspf1d8n2d.poc.infoblox.local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmUuMTczLjE4L"
                           "jAuMTAu:xxx.xxx.xxx.xxx/xtndspf1d8n2e.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'xtndspf1d8n2e.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJl:"
                           "xtndspf1d8n2e.poc.infoblox.local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmYuMTczLjE4L"
                           "jAuMTEyLg:xxx.xxx.xxx.xxx/xtndspf1d8n2f.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'xtndspf1d8n2f.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJm:xtndspf1d8"
                           "n2f.poc.infoblox.local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmcuMTczLjE4L"
                           "jAuMTEu:xxx.xxx.xxx.xxx/xtndspf1d8n2g.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'xtndspf1d8n2g.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJn:"
                           "xtndspf1d8n2g.poc.infoblox.local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmguMTczLjE4Lj"
                           "AuMTEyLg:xxx.xxx.xxx.xxx/xtndspf1d8n2h.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'xtndspf1d8n2h.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJo:xtndspf1d8"
                           "n2h.poc.infoblox.local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmEuMTAuMC4xLjIzNi4:xxx.xxx"
                           ".xxx.xxx/a.poc.infoblox.local/default', 'configure_for_dhcp': False, "
                           "'host': 'a.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5h:a.poc.infoblox.local"
                           "/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmZvby4xMC4wLjEuMC4:xxx.xxx"
                           ".xxx.xxx/foo.poc.infoblox.local/default', 'configure_for_dhcp': False, "
                           "'host': 'foo.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5mb28:foo.poc.infoblox"
                           ".local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmJsYS4xMC4wLjAuMS4:xxx.xxx"
                           ".xxx.xxx/bla.poc.infoblox.local/default', 'configure_for_dhcp': False, "
                           "'host': 'bla.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5ibGE:bla.poc.infoblox"
                           ".local/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuY29tLmZvby4uMTAuMTAuMTAuMjAu:xxx.xxx.xxx.xxx/foo.com"
                           "/default', 'configure_for_dhcp': False, 'host': 'foo.com', 'ipv4addr': 'xxx.xxx.xxx.xxx'} "
                           "| record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5mb28u:foo.com/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLi4xLjEuMS4xLg:xxx.xxx.xxx"
                           ".xxx/poc.infoblox.local/default', 'configure_for_dhcp': False, "
                           "'host': 'poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy4:poc.infoblox.local"
                           "/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuY29tLmZvby5rYWthLjEuMS4xLjEwLg:xxx.xxx.xxx.xxx/kaka"
                           ".foo.com/default', 'configure_for_dhcp': False, 'host': 'kaka.foo.com', 'ipv4addr': "
                           "'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5mb28ua2FrYQ:kaka.foo.com/default |\n"
                           "| {'_ref': 'record:host_ipv4addr"
                           "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLm1hY2FyZW5hLjEwLjEwLjEwLjIwL"
                           "g:xxx.xxx.xxx.xxx/macarena.poc.infoblox.local/default', 'configure_for_dhcp': "
                           "False, 'host': 'macarena.poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc"
                           "3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ:macarena.poc.infoblox.local/"
                           "default |\n"),
        "context": {
            "Infoblox.Host(val.ReferenceID && val.ReferenceID === obj.ReferenceID)": [
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJj"
                                   ":xtndspf1d8n2c.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmMu"
                                    "MTczLjE4LjAuNS4:xxx.xxx.xxx.xxx/xtndspf1d8n2c.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "xtndspf1d8n2c.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJk"
                                   ":xtndspf1d8n2d.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMm"
                                    "QuMTczLjE4LjAuMTAu:xxx.xxx.xxx.xxx/xtndspf1d8n2d.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "xtndspf1d8n2d.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJl"
                                   ":xtndspf1d8n2e.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMm"
                                    "UuMTczLjE4LjAuMTAu:xxx.xxx.xxx.xxx/xtndspf1d8n2e.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "xtndspf1d8n2e.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJm"
                                   ":xtndspf1d8n2f.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmY"
                                    "uMTczLjE4LjAuMTEyLg:xxx.xxx.xxx.xxx/xtndspf1d8n2f.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "xtndspf1d8n2f.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJn"
                                   ":xtndspf1d8n2g.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmc"
                                    "uMTczLjE4LjAuMTEu:xxx.xxx.xxx.xxx/xtndspf1d8n2g.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "xtndspf1d8n2g.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJo"
                                   ":xtndspf1d8n2h.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmgu"
                                    "MTczLjE4LjAuMTEyLg:xxx.xxx.xxx.xxx/xtndspf1d8n2h.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "xtndspf1d8n2h.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5h:a.poc.infoblox"
                                   ".local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmEuMTAuMC4xLjIzNi4"
                                    ":xxx.xxx.xxx.xxx/a.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "a.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5mb28:foo.poc"
                                   ".infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmZvby4xMC4wLjEuMC4"
                                    ":xxx.xxx.xxx.xxx/foo.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "foo.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5ibGE:bla.poc"
                                   ".infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmJsYS4xMC4wLjAuMS4"
                                    ":xxx.xxx.xxx.xxx/bla.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "bla.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5mb28u:foo.com/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuY29tLmZvby4uMTAuMTAuMTAuMjAu:xxx.xxx.xxx"
                                    ".xxx/foo.com/default",
                            "configure_for_dhcp": False,
                            "host": "foo.com",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy4:poc.infoblox"
                                   ".local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLi4xLjEuMS4xLg:xxx"
                                    ".xxx.xxx.xxx/poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5mb28ua2FrYQ:kaka.foo.com/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuY29tLmZvby5rYWthLjEuMS4xLjEwLg:xxx.xxx.xxx"
                                    ".xxx/kaka.foo.com/default",
                            "configure_for_dhcp": False,
                            "host": "kaka.foo.com",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                },
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ"
                                   ":macarena.poc.infoblox.local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLm1hY2FyZW5hLjEwLjEw"
                                    "LjEwLjIwLg:xxx.xxx.xxx.xxx/macarena.poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "macarena.poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ]
                }
            ]
        },
        "raw_response": {"result": [
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJj"
                        ":xtndspf1d8n2c.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmMuMT"
                                "czLjE4LjAuNS4:xxx.xxx.xxx.xxx/xtndspf1d8n2c.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "xtndspf1d8n2c.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJk"
                        ":xtndspf1d8n2d.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0bmRzcGYxZDhuMmQuMTc"
                                "zLjE4LjAuMTAu:xxx.xxx.xxx.xxx/xtndspf1d8n2d.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "xtndspf1d8n2d.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJl:xtndspf1d8n2"
                        "e.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh0"
                                "bmRzcGYxZDhuMmUuMTczLjE4LjAuMTAu:xxx.xxx.xxx.xxx/xtndspf1d8n2e.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "xtndspf1d8n2e.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJm:xtndspf1d8n"
                        "2f.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh"
                                "0bmRzcGYxZDhuMmYuMTczLjE4LjAuMTEyLg:xxx.xxx.xxx.xxx/xtndspf1d8n2f.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "xtndspf1d8n2f.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJn:xtndspf1d8n"
                        "2g.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLn"
                                "h0bmRzcGYxZDhuMmcuMTczLjE4LjAuMTEu:xxx.xxx.xxx.xxx/xtndspf1d8n2g.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "xtndspf1d8n2g.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy54dG5kc3BmMWQ4bjJo:xtndspf1d8"
                        "n2h.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLnh"
                                "0bmRzcGYxZDhuMmguMTczLjE4LjAuMTEyLg:xxx.xxx.xxx.xxx/xtndspf1d8n2h.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "xtndspf1d8n2h.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5h:a.poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmE"
                                "uMTAuMC4xLjIzNi4:xxx.xxx.xxx.xxx/a.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "a.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5mb28:foo.poc.infoblox.local/"
                        "default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmZ"
                                "vby4xMC4wLjEuMC4:xxx.xxx.xxx.xxx/foo.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "foo.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5ibGE:bla.poc.infoblox.local/"
                        "default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLmJ"
                                "sYS4xMC4wLjAuMS4:xxx.xxx.xxx.xxx/bla.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "bla.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5mb28u:foo.com/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuY29tLmZvby4uMTAuMTAuMTAuMj"
                                "Au:xxx.xxx.xxx.xxx/foo.com/default",
                        "configure_for_dhcp": False,
                        "host": "foo.com",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy4:poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLi4"
                                "xLjEuMS4xLg:xxx.xxx.xxx.xxx/poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmNvbS5mb28ua2FrYQ:kaka.foo.com/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuY29tLmZvby5rYWthLjEuMS4xLjEwLg:xxx.xxx.xxx.xxx"
                                "/kaka.foo.com/default",
                        "configure_for_dhcp": False,
                        "host": "kaka.foo.com",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            },
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ:macarena.poc"
                        ".infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLm1hY2FyZW5hLjEwLjEwLjEw"
                                "LjIwLg:xxx.xxx.xxx.xxx/macarena.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "macarena.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            }
        ]}
    }
    TEST_SEARCH_HOST_RECORD_DATA = {
        "args": {"name": "poc.infoblox.local"},
        "human_readable": ("### Infoblox Integration - Search for a Host Record: poc.infoblox.local\n"
                           "|Ipv 4 Addrs|Name|Reference ID|View|\n"
                           "|---|---|---|---|\n"
                           "| {'_ref': 'record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3guc"
                           "G9jLi4xLjEuMS4xLg:xxx.xxx.xxx.xxx/poc.infoblox.local/default', 'configure_for_dhcp': False"
                           ", 'host': 'poc.infoblox.local', 'ipv4addr': 'xxx.xxx.xxx.xxx'} | poc.infoblox.local | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy4:poc.infoblox.local"
                           "/default | default |\n"),
        "context": {
            "Infoblox.Host(val.ReferenceID && val.ReferenceID === obj.ReferenceID)": [
                {
                    "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy4:poc.infoblox"
                                   ".local/default",
                    "Ipv4addrs": [
                        {
                            "_ref": "record:host_ipv4addr"
                                    "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLi4xLjEuMS4xLg:xxx"
                                    ".xxx.xxx.xxx/poc.infoblox.local/default",
                            "configure_for_dhcp": False,
                            "host": "poc.infoblox.local",
                            "ipv4addr": "xxx.xxx.xxx.xxx"
                        }
                    ],
                    "Name": "poc.infoblox.local",
                    "View": "default"
                }
            ]
        },
        "raw_response": {"result": [
            {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy4:poc.infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLi4xLjEuMS4xLg:xxx.xxx"
                                ".xxx.xxx/poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ],
                "name": "poc.infoblox.local",
                "view": "default"
            }
        ]}
    }
    TEST_CREATE_A_RECORD_DATA = {
        "args": {"name": "poc.infoblox.local", "ipv4addr": "xxx.xxx.xxx.xxx"},
        "human_readable": ("### Infoblox Integration - A Record: poc.infoblox.local has been created:\n"
                           "|Disable|Ipv 4 Addr|Name|Reference ID|Type|View|\n"
                           "|---|---|---|---|---|---|\n"
                           "| false | xxx.xxx.xxx.xxx | poc.infoblox.local | "
                           "record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLCwyNTAuMjUwLjI1MC4yNTA:poc"
                           ".infoblox.local/default | record:a | default |\n"),
        "context": {
            'Infoblox.ARecord(val.ReferenceID && val.ReferenceID === obj.ReferenceID)': [{
                "ReferenceID": "record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLCwyNTAuMjUwLjI1MC4yNTA"
                               ":poc.infoblox.local/default",
                "Disable": False,
                "Ipv4addr": "xxx.xxx.xxx.xxx",
                "Name": "poc.infoblox.local",
                "View": "default",
                "Type": "record:a"
            }]
        },
        "raw_response": {"result": {
            "_ref": "record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLCwyNTAuMjUwLjI1MC4yNTA:poc"
                    ".infoblox.local/default",
            "disable": False,
            "ipv4addr": "xxx.xxx.xxx.xxx",
            "name": "poc.infoblox.local",
            "view": "default",
            "type": "record:a"
        }}
    }
    TEST_ADD_HOST_RECORD_DATA = {
        "args": {'host': 'koko.poc.infoblox.local', 'ipadd': 'xxx.xxx.xxx.xxx'},
        "human_readable": (
            "### Infoblox Integration - Host Record koko.poc.infoblox.local with IP address xxx.xxx.xxx.xxx was "
            "added successfully with reference\n"
            "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5rb2tv:koko.poc.infoblox.local/default\n"
            "|Reference ID|\n"
            "|---|\n"
            "| record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5rb2tv:koko.poc.infoblox.local/default |\n"
        ),
        "context": {
            "Infoblox.Host(val.ReferenceID && val.ReferenceID === obj.ReferenceID)": {
                "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5rb2tv:koko.poc.info"
                               "blox.local/default"
            }
        },
        "raw_response": {
            "result": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5rb2tv:koko.poc.info"
                      "blox.local/default"
        }
    }
    TEST_UPDATE_HOST_IP_DATA = {
        "args": {
            "ref_id": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ:macarena.poc.info"
                      "blox.local/default",
            "ipv4addr": "xxx.xxx.xxx.xxx"
        },
        "human_readable": ("### Infoblox Integration - Updated a Host's IP with new IP address: xxx.xxx.xxx.xxx\n"
                           "|Ipv 4 Addrs|Reference ID|\n"
                           "|---|---|\n"
                           "| {'_ref': 'record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3guc"
                           "G9jLm1hY2FyZW5hLjEwLjEwLjEwLjQyLg:xxx.xxx.xxx.xxx/macarena.poc.infoblox.local/default', "
                           "'configure_for_dhcp': False, 'host': 'macarena.poc.infoblox.local', 'ipv4addr': "
                           "'xxx.xxx.xxx.xxx'} | "
                           "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ:macarena.poc"
                           ".infoblox.local/default |\n"),
        "context": {
            "Infoblox.Host(val.ReferenceID && val.ReferenceID === obj.ReferenceID)": [{
                "ReferenceID": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ:macarena"
                               ".poc.infoblox.local/default",
                "Ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLm1hY2FyZW5hLjEwLjEwLjEwL"
                                "jQyLg:xxx.xxx.xxx.xxx/macarena.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "macarena.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            }]
        },
        "raw_response": {
            "result": {
                "_ref": "record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmxvY2FsLmluZm9ibG94LnBvYy5tYWNhcmVuYQ:macarena.poc"
                        ".infoblox.local/default",
                "ipv4addrs": [
                    {
                        "_ref": "record:host_ipv4addr"
                                "/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQubG9jYWwuaW5mb2Jsb3gucG9jLm1hY2FyZW5hLjEwLjEwLjEwL"
                                "jQyLg:xxx.xxx.xxx.xxx/macarena.poc.infoblox.local/default",
                        "configure_for_dhcp": False,
                        "host": "macarena.poc.infoblox.local",
                        "ipv4addr": "xxx.xxx.xxx.xxx"
                    }
                ]
            }
        }
    }
    TEST_UPDATE_A_RECORD_DATA = {
        "args": {
            "ref_id": "record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQuY29tLmZvbyxrYWthLDEuMi4zLjQ:kaka.foo.com/default",
            "ipv4addr": "xxx.xxx.xxx.xxx",
            "name": "infoblw.foo.com",
            "comment": "infotest!"
        },
        "human_readable": (
            "### Infoblox Integration - Updated a Host Record with the ReferenceID: record:a/ZG5zLmJpbmRfYSQuX2RlZmF1"
            "bHQuY29tLmZvbyxrYWthLDEuMi4zLjQ:kaka.foo.com/default with IP address: xxx.xxx.xxx.xxx\n"
            "|Reference ID|\n"
            "|---|\n"
            "| record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQuY29tLmZvbyxpbmZvYmx3LDUuNi43Ljg:infoblw.foo.com/default |\n"),
        "context": {
            "Infoblox.ARecord(val.ReferenceID && val.ReferenceID === obj.ReferenceID)": {
                "ReferenceID": "record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQuY29tLmZvbyxpbmZvYmx3LDUuNi43Ljg:info"
                               "blw.foo.com/default"
            }
        },
        "raw_response": {
            "result": "record:a/ZG5zLmJpbmRfYSQuX2RlZmF1bHQuY29tLmZvbyxpbmZvYmx3LDUuNi43Ljg:infoblw.foo.com/default"
        }
    }

    @pytest.mark.parametrize(
        "infoblox_function, test_data",
        [
            (list_records_command, TEST_LIST_RECORDS_DATA),
            (list_hosts_command, TEST_LIST_HOSTS_DATA),
            (search_host_record_command, TEST_SEARCH_HOST_RECORD_DATA),
            (create_a_record_command, TEST_CREATE_A_RECORD_DATA),
            (add_host_record_command, TEST_ADD_HOST_RECORD_DATA),
            (update_host_ip_command, TEST_UPDATE_HOST_IP_DATA),
            (update_a_record_command, TEST_UPDATE_A_RECORD_DATA)
        ]
    )
    def test_record(self, mocker, infoblox_function, test_data):
        mocker.patch.object(client, '_http_request', return_value=test_data["raw_response"])
        human_readable, context, raw_response = infoblox_function(client, test_data["args"])
        assert human_readable == test_data["human_readable"]
        assert context == test_data["context"]
        assert raw_response == test_data["raw_response"]
