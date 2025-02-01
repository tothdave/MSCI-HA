import unittest
from unittest.mock import patch, mock_open
import argparse
import pandas as pd
import os
from filelock import Timeout
from ip_tool import (
    file_lock,
    IP_RANGES_FILE_PATH,
    get_and_save_ip_ranges,
    save_ip_ranges,
    get_ip_ranges,
    netmask_to_cidr,
    check_collisions,
    main
)

class TestIPTool(unittest.TestCase):
    
    @patch("ip_tool.get_ip_ranges")
    @patch("ip_tool.save_ip_ranges")
    @patch("ip_tool.file_lock")
    def test_get_and_save_ip_ranges(self, mock_filelock, mock_save_ip_ranges, mock_get_ip_ranges):
        mock_get_ip_ranges.return_value = ["192.168.1.1/24"]

        get_and_save_ip_ranges()

        mock_get_ip_ranges.assert_called()
        mock_save_ip_ranges.assert_called_with(["192.168.1.1/24"])

    @patch("ip_tool.get_ip_ranges")
    @patch("ip_tool.save_ip_ranges")
    @patch("ip_tool.file_lock")
    def test_get_and_save_ip_ranges_timeout_error(self, mock_filelock, mock_save_ip_ranges, mock_get_ip_ranges):
        mock_filelock.__enter__.side_effect = Timeout(file_lock)

        with patch("builtins.open", mock_open(read_data="POD_NAME 192.168.0.1/32")) as mock_file:
            get_and_save_ip_ranges()
            mock_save_ip_ranges.assert_not_called()

    @patch("ip_tool.get_ip_ranges")
    @patch("ip_tool.save_ip_ranges")
    @patch("ip_tool.file_lock")
    def test_get_and_save_ip_ranges_generic_error(self, mock_filelock, mock_save_ip_ranges, mock_get_ip_ranges):
        mock_filelock.__enter__.side_effect = Exception(file_lock)

        with patch("builtins.open", mock_open(read_data="POD_NAME 192.168.0.1/32")) as mock_file:
            get_and_save_ip_ranges()
            mock_save_ip_ranges.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("ip_tool.file_lock")
    def test_save_ip_ranges(self, mock_filelock, mock_open):
        ip_ranges = ["192.168.1.1/24", "10.0.0.1/16"]

        save_ip_ranges(ip_ranges)

        mock_open.assert_called_with(IP_RANGES_FILE_PATH, "a")
        mock_open().write.assert_any_call("POD_NAME,192.168.1.1/24\n")
        mock_open().write.assert_any_call("POD_NAME,10.0.0.1/16\n")


    @patch("builtins.open", side_effect=Exception("Test exception"))
    @patch("ip_tool.file_lock")
    def test_save_ip_ranges_error(self, mock_filelock, mock_open):
        ip_ranges = ["192.168.1.1/24", "10.0.0.1/16"]

        with self.assertLogs(level="ERROR") as log:
            save_ip_ranges(ip_ranges)
            self.assertIn("Test exception", log.output[0])

    @patch("ip_tool.netifaces.interfaces")
    @patch("ip_tool.netifaces.ifaddresses")
    def test_get_ip_ranges(self, mock_ifaddresses, mock_interfaces):
        mock_interfaces.return_value = ["eth0", "eth1"]
        mock_ifaddresses.side_effect = [
            {
                2: [
                    {"addr": "192.168.1.1", "netmask": "255.255.255.0"},
                ]
            },
            {},
        ]

        expected_result = ["192.168.1.1/24"]
        result = get_ip_ranges()
        self.assertEqual(result, expected_result)

    def test_netmask_to_cidr(self):
        netmask = "255.255.255.0"
        expected_cidr = 24
        result = netmask_to_cidr(netmask)
        self.assertEqual(result, expected_cidr)

    @patch("pandas.read_csv")
    @patch("pandas.DataFrame.to_csv")
    @patch("ip_tool.os.makedirs")
    def test_check_collisions(self, mock_makedirs, mock_to_csv, mock_read_csv):
        mock_read_csv.return_value = pd.DataFrame(
            {
                "container_id": ["container1", "container2"],
                "ip_range": ["192.168.1.0/24", "192.168.1.128/25"],
            }
        )

        result = check_collisions("test_file.csv")

        self.assertFalse(result.empty)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["container1"], "container1")
        self.assertEqual(result.iloc[0]["container2"], "container2")
        mock_makedirs.assert_called()
        mock_to_csv.assert_called()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("ip_tool.get_and_save_ip_ranges")
    def test_main_get_ip_ranges(self, mock_get_and_save_ip_ranges, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(check_collision=None)

        main()
        mock_get_and_save_ip_ranges.assert_called()

    @patch("argparse.ArgumentParser.parse_args")
    @patch("ip_tool.check_collisions")
    def test_main_check_collisions(self, mock_check_collisions, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(check_collision="test_file.csv")

        main()
        mock_check_collisions.assert_called_with("test_file.csv")

    