from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
import uuid
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock

import makerbot_driver


class TestMachineFactor(unittest.TestCase):

    def setUp(self):
        self.factory = makerbot_driver.MachineFactory()

    def tearDown(self):
        self.factory = None

    def test_get_profile_regex_bot_not_found(self):
        bot_dict = {
            'fw_version': -000
        }
        expected_regex = None
        self.assertEqual(
            expected_regex, self.factory.get_profile_regex(bot_dict))

#  def test_get_profile_regex_hax_vid_pid_bot_found(self):
#    bot_dict = {
#        'fw_version' : 506,
#        'vid' : 0x23c1,
#        'pid' : 0xd314,
#        'tool_count'  : 1,
#        }
#    expected_regex = '.*ReplicatorSingle.*'
#    self.assertEqual(expected_regex, self.factory.get_profile_regex(bot_dict))

    def test_get_profile_regex_had_vid_pid_rep2(self):
        bot_dict = {
            'fw_version': 600,
            'vid': 0x23C1,
            'pid': 0xB015,
        }
        expected_regex = '.*Replicator2'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tom(self):
        bot_dict = {
            'fw_version': 300,
            'vid': 0x0403,
            'pid': 0x6001,
        }
        expected_regex = '.*TOM.*'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tool_count_1(self):
        bot_dict = {
            'fw_version': 506,
            'vid': 0x23c1,
            'pid': 0xd314,
            'tool_count': 1,
        }
        expected_regex = '.*ReplicatorSingle'
        result = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, result)

    def test_get_profile_regex_has_vid_pid_tool_count_2(self):
        bot_dict = {
            'fw_version': 506,
            'vid': 0x23c1,
            'pid': 0xd314,
            'tool_count': 2,
        }
        expected_regex = '.*ReplicatorDual'
        match = self.factory.get_profile_regex(bot_dict)
        self.assertEqual(expected_regex, match)


class TestBuildFromPortMockedMachineInquisitor(unittest.TestCase):
    def setUp(self):
        self.s3g_mock = mock.Mock(makerbot_driver.s3g)
        self.inquisitor = makerbot_driver.MachineInquisitor('/dev/dummy_port')
        self.inquisitor.create_s3g = mock.Mock()
        self.inquisitor.create_s3g.return_value = self.s3g_mock
        self.factory = makerbot_driver.MachineFactory()
        self.factory.create_inquisitor = mock.Mock()
        self.factory.create_inquisitor.return_value = self.inquisitor

    def test_build_from_port_low_version_number(self):
        version = 000
        self.s3g_mock.get_version.return_value = version
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        expected_s3g = None
        expected_profile = None
        expected_parser = None
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertEqual(expected_s3g, getattr(return_obj, 's3g'))
        self.assertEqual(expected_profile, getattr(return_obj, 'profile'))
        self.assertEqual(expected_parser, getattr(return_obj, 'gcodeparser'))

#    @unittest.skip("This functionality has been disabled for now")
    def test_build_from_port_version_number_500_tool_count_1_Replicator(self):
        #Time to mock all of s3g's version!
        version = 500
        tool_count = 1
        vid, pid = 0x23C1, 0xD314
        verified_status = True
        proper_name = 'test_bot'
        self.s3g_mock.get_version = mock.Mock(return_value=version)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_verified_status = mock.Mock(
            return_value=verified_status)
        self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS%i' % (version)
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorSingle')
        expected_profile.values['print_to_file_type']=['s3g']
        expected_profile.values['machine_name'] = proper_name          
        expected_parser = makerbot_driver.Gcode.GcodeParser()
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

    def test_build_from_port_version_number_500_tool_count_2_mightyboard(self):
        #Time to mock all of s3g's version!
        version = 500
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        verified_status = True
        proper_name = 'test_bot'
        self.s3g_mock.get_version = mock.Mock(return_value=version)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_verified_status = mock.Mock(
            return_value=verified_status)
        self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS%i' % (version)
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorDual')
        expected_profile.values['print_to_file_type']=['s3g']
        expected_profile.values['machine_name'] = proper_name          
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

    def test_build_from_port_x3g_version(self):
        #Time to mock all of s3g's version!
        # the version number for x3g is 700, but the decision should be based on the "SoftwareVariant" flag only
        version = 600 
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        verified_status = True
        proper_name = 'test_bot'
        advanced_version_info = {
            'Version': version,
            'InternalVersion': 0,
            'SoftwareVariant': 1,
            'ReservedA': 0,
            'ReservedB': 0,
        }
        self.s3g_mock.get_version = mock.Mock(return_value=version)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_verified_status = mock.Mock(
            return_value=verified_status)
        self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock()
        self.s3g_mock.get_advanced_version.return_value = advanced_version_info
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS%i' % (version)
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorDual')
        expected_profile.values['print_to_file_type']=['x3g']
        expected_profile.values['machine_name'] = proper_name          
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.s3g_mock.set_print_to_file_type.assert_called_once_with('x3g')
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)

    def test_build_from_port_s3g_version(self):
        #Time to mock all of s3g's version!
        version = 600
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        verified_status = True
        proper_name = 'test_bot'
        advanced_version_info = {
            'Version': version,
            'InternalVersion': 0,
            'SoftwareVariant': 0,
            'ReservedA': 0,
            'ReservedB': 0,
        }
        self.s3g_mock.get_version = mock.Mock(return_value=version)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_verified_status = mock.Mock(
            return_value=verified_status)
        self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_version = mock.Mock()
        self.s3g_mock.get_advanced_version.return_value = advanced_version_info
        #Mock the returned s3g obj
        expected_mock_s3g_obj = 'SUCCESS%i' % (version)
        self.factory.create_s3g = mock.Mock()
        self.factory.create_s3g.return_value = expected_mock_s3g_obj
        expected_profile = makerbot_driver.Profile('ReplicatorDual')
        expected_profile.values['print_to_file_type']=['s3g']
        expected_profile.values['machine_name'] = proper_name          
        return_obj = self.factory.build_from_port('/dev/dummy_port')
        self.assertTrue(getattr(return_obj, 's3g') is not None)
        self.s3g_mock.set_print_to_file_type.assert_called_once_with('s3g')
        self.assertEqual(
            expected_profile.values, getattr(return_obj, 'profile').values)
        self.assertTrue(getattr(return_obj, 'gcodeparser') is not None)


class TestMachineInquisitor(unittest.TestCase):
    def setUp(self):
        self.inquisitor = makerbot_driver.MachineInquisitor('/dev/dummy_port')
        self.s3g_mock = mock.Mock(makerbot_driver.s3g)
        self.inquisitor.create_s3g = mock.Mock(return_value=self.s3g_mock)

    def tearDown(self):
        self.inquisitor = None

    def test_low_version(self):
        version = 000
        self.s3g_mock.get_version.return_value = version
        self.s3g_mock.set_print_to_file_type('s3g')
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        expected_settings = {'fw_version': version, 'print_to_file_type':'s3g'}
        s3g, got_settings = self.inquisitor.query()
        self.assertEqual(s3g, self.s3g_mock)
        self.assertEqual(expected_settings, got_settings)

    def test_version_500_has_random_uuid(self):
        #Time to mock all of s3g's version!
        version = 500
        tool_count = 2
        vid, pid = 0x23C1, 0xB404
        verified_status = True
        proper_name = 'test_bot'
        self.s3g_mock.get_version = mock.Mock(return_value=version)
        self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
        self.s3g_mock.get_verified_status = mock.Mock(
            return_value=verified_status)
        self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
        self.s3g_mock.get_vid_pid = mock.Mock()
        self.s3g_mock.get_vid_pid.return_value = vid, pid
        self.s3g_mock.get_advanced_name = mock.Mock()
        self.s3g_mock.get_advanced_version = mock.Mock(side_effect=makerbot_driver.CommandNotSupportedError)
        (s3g, got_settings) = self.inquisitor.query()
        #Random uuids have two bytes which have constaints on them
        rand_uuid = got_settings['uuid']
        str_uuid = str(rand_uuid)
        self.assertEqual(str_uuid[14], '4')
        self.assertTrue(
            int(str_uuid[19], 16) >= 0x8 and int(str_uuid[19], 16) <= 0xb)

if __name__ == '__main__':
    unittest.main()
