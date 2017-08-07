"""
Test base helpers.
"""

# Python3 support
from __future__ import print_function
from __future__ import unicode_literals

# Python std lib
import os
import sys
import unittest

# third party libs
try:
    import jinja2  # noqa
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False

try:
    import jtextfsm as textfsm  # noqa
    HAS_TEXTFSM = True
except ImportError:
    HAS_TEXTFSM = False

try:
    from lxml import etree as ET
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

try:
    from netaddr.core import AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

# NAPALM base
import napalm_base.helpers
import napalm_base.exceptions
from napalm_base.base import NetworkDriver
from napalm_base.mock import MockDriver
from napalm_base.utils.string_parsers import convert_uptime_string_seconds


class TestBaseHelpers(unittest.TestCase):
    """Test helpers functions."""

    @classmethod
    def setUpClass(cls):
        cls.network_driver = FakeNetworkDriver()
        # neded when calling helpers

    def test_load_template(self):
        """
        Tests the helper function ```load_template```:

            * check if raises TemplateNotImplemented when trying to use inexisting template
            * check if can load empty template
            * check if raises TemplateRenderException when template is not correctly formatted
            * check if can load correct template
            * check if raises IOError if invalid path is specified
            * check if raises TemplateNotImplemented when trying to use inexisting template in
              custom path
            * check if can load correct template from custom path
            * check if template passed as string can be loaded
            * check that the search path setup by MRO is correct when loading an incorrecet template
        """
        class TestDriver(MockDriver):
            pass


        self.assertTrue(HAS_JINJA)  # firstly check if jinja2 is installed
        _NTP_PEERS_LIST = [
            '172.17.17.1',
            '172.17.17.2'
        ]
        _TEMPLATE_VARS = {
            'peers': _NTP_PEERS_LIST
        }

        self.assertRaises(napalm_base.exceptions.TemplateNotImplemented,
                          napalm_base.helpers.load_template,
                          self.network_driver,
                          '__this_template_does_not_exist__',
                          **_TEMPLATE_VARS)

        self.assertTrue(napalm_base.helpers.load_template(self.network_driver,
                                                          '__empty_template__',
                                                          **_TEMPLATE_VARS))

        self.assertRaises(napalm_base.exceptions.TemplateRenderException,
                          napalm_base.helpers.load_template,
                          self.network_driver,
                          '__completely_wrong_template__',
                          **_TEMPLATE_VARS)

        self.assertTrue(napalm_base.helpers.load_template(self.network_driver,
                                                          '__a_very_nice_template__',
                                                          **_TEMPLATE_VARS))

        self.assertRaises(IOError,
                          napalm_base.helpers.load_template,
                          self.network_driver,
                          '__a_very_nice_template__',
                          template_path='/this/path/does/not/exist',
                          **_TEMPLATE_VARS)

        install_dir = os.path.dirname(
            os.path.abspath(sys.modules[self.network_driver.__module__].__file__))
        custom_path = os.path.join(install_dir, '../custom/path/base')

        self.assertRaises(napalm_base.exceptions.TemplateNotImplemented,
                          napalm_base.helpers.load_template,
                          self.network_driver,
                          '__this_template_does_not_exist__',
                          template_path=custom_path,
                          **_TEMPLATE_VARS)

        self.assertTrue(napalm_base.helpers.load_template(self.network_driver,
                                                          '__a_very_nice_template__',
                                                          template_path=custom_path,
                                                          **_TEMPLATE_VARS))

        template_source = '{% for peer in peers %}ntp peer {{peer}}\n{% endfor %}'

        self.assertTrue(napalm_base.helpers.load_template(self.network_driver,
                                                          '_this_still_needs_a_name',
                                                          template_source=template_source,
                                                          **_TEMPLATE_VARS))
        self.assertRaisesRegexp(napalm_base.exceptions.TemplateNotImplemented,
                                "search path.*napalm-base/test/unit/templates',.*napalm-base/napalm_base/templates']",
                                napalm_base.helpers.load_template,
                                self.network_driver,
                                '__this_template_does_not_exist__',
                                **_TEMPLATE_VARS)


    def test_textfsm_extractor(self):
        """
        Tests the helper function ```textfsm_extractor```:

            * check if raises TemplateNotImplemented when template is not defined
            * check if raises TemplateRenderException when template is empty
            * check if raises TemplateRenderException when template is not properly defined
            * check if returns a non-empty list as output
        """

        self.assertTrue(HAS_TEXTFSM)  # before anything else, let's see if TextFSM is available
        _TEXTFSM_TEST_STRING = '''
        Groups: 3 Peers: 3 Down peers: 0
        Table          Tot Paths  Act Paths Suppressed    History Damp State    Pending
        inet.0               947        310          0          0          0          0
        inet6.0              849        807          0          0          0          0
        Peer                     AS      InPkt     OutPkt    OutQ   Flaps Last Up/Dwn State|#Active/Received/Damped...  #noqa
        10.247.68.182         65550     131725   28179233       0      11     6w3d17h Establ
          inet.0: 4/5/1
          inet6.0: 0/0/0
        10.254.166.246        65550     136159   29104942       0       0      6w5d6h Establ
          inet.0: 0/0/0
          inet6.0: 7/8/1
        192.0.2.100           65551    1269381    1363320       0       1      9w5d6h 2/3/0 0/0/0
        '''

        self.assertRaises(napalm_base.exceptions.TemplateNotImplemented,
                          napalm_base.helpers.textfsm_extractor,
                          self.network_driver,
                          '__this_template_does_not_exist__',
                          _TEXTFSM_TEST_STRING)

        self.assertRaises(napalm_base.exceptions.TemplateRenderException,
                          napalm_base.helpers.textfsm_extractor,
                          self.network_driver,
                          '__empty_template__',
                          _TEXTFSM_TEST_STRING)

        self.assertRaises(napalm_base.exceptions.TemplateRenderException,
                          napalm_base.helpers.textfsm_extractor,
                          self.network_driver,
                          '__completely_wrong_template__',
                          _TEXTFSM_TEST_STRING)

        self.assertIsInstance(napalm_base.helpers.textfsm_extractor(self.network_driver,
                                                                    '__a_very_nice_template__',
                                                                    _TEXTFSM_TEST_STRING),
                              list)

    def test_convert(self):
        """
        Tests helper function ```convert```:

            * cast of non-int str to int returns default value
            * cast of str to float returns desired float-type value
            * cast of None obj to string does not cast, but returns default
        """
        self.assertTrue(napalm_base.helpers.convert(int, 'non-int-value', default=-100) == -100)
        # default value returned
        self.assertIsInstance(napalm_base.helpers.convert(float, '1e-17'), float)
        # converts indeed to float
        self.assertFalse(napalm_base.helpers.convert(str, None) == 'None')
        # should not convert None-type to 'None' string
        self.assertTrue(napalm_base.helpers.convert(str, None) == u'')
        # should return empty unicode

    def test_find_txt(self):

        """
        Tests helper function ```find_txt```:

            * check if returns default when retrieving from wrong path
            * check if non-empty string inside existing tag
            * check if can parse boolean values as text
            * check if can retrieve int values
        """

        self.assertTrue(HAS_LXML)  # firstly check if lxml is installed

        _XML_STRING = '''
        <family>
            <parent1>
                <child1>
                    Hi, I am child1 of parent1.
                </child1>
                <child2>
                    Hi, I am child2 of parent1.
                </child2>
                <child3>
                    Hi, I am child3 of parent1.
                </child3>
            </parent1>
            <parent2>
                <child1>
                    Hi, I am child1 of parent2.
                </child1>
                <child2 special="true">
                    Haha.
                </child2>
            </parent2>
            <parent3 lonely="true"></parent3>
            <stats>
                <parents>3</parents>
                <children>4</children>
            </stats>
        </family>
        '''

        _XML_TREE = ET.fromstring(_XML_STRING)

        self.assertFalse(napalm_base.helpers.find_txt(_XML_TREE, 'parent100/child200', False))
        # returns default value (in this case boolean value False)

        # check if content inside the tag /parent1/child1
        self.assertTrue(len(napalm_base.helpers.find_txt(_XML_TREE, 'parent1/child1')) > 0)

        # check if able to eval boolean returned as text inside the XML tree
        self.assertTrue(
            eval(napalm_base.helpers.find_txt(_XML_TREE, 'parent3/@lonely', 'false').title()))

        # int values
        self.assertIsInstance(
            int(napalm_base.helpers.find_txt(_XML_TREE, 'stats/parents')), int)

        # get first match of the tag child3, wherever would be
        _CHILD3_TAG = _XML_TREE.find('.//child3')

        # check if content inside the discovered tag child3
        self.assertTrue(len(napalm_base.helpers.find_txt(_CHILD3_TAG, '.')) > 0)

        _SPECIAL_CHILD2 = _XML_TREE.find('.//child2[@special="true"]')

        self.assertTrue(len(napalm_base.helpers.find_txt(_SPECIAL_CHILD2, '.')) > 0)

        _SPECIAL_CHILD100 = _XML_TREE.find('.//child100[@special="true"]')

        self.assertFalse(len(napalm_base.helpers.find_txt(_SPECIAL_CHILD100, '.')) > 0)

        _NOT_SPECIAL_CHILD2 = _XML_TREE.xpath('.//child2[not(@special="true")]')[0]
        # use XPath to get tags using predicates!

        self.assertTrue(len(napalm_base.helpers.find_txt(_NOT_SPECIAL_CHILD2, '.')) > 0)

    def test_mac(self):

        """
        Tests the helper function ```mac```:

            * check if raises AddrFormatError when invalid MAC
            * check if MAC address returned as expected
        """

        self.assertTrue(HAS_NETADDR)

        # test that raises AddrFormatError when wrong format
        self.assertRaises(AddrFormatError, napalm_base.helpers.mac, 'fake')

        self.assertEqual(napalm_base.helpers.mac('0123456789ab'), '01:23:45:67:89:AB')
        self.assertEqual(napalm_base.helpers.mac('0123.4567.89ab'), '01:23:45:67:89:AB')
        self.assertEqual(napalm_base.helpers.mac('123.4567.89ab'), '01:23:45:67:89:AB')

    def test_ip(self):
        """
        Tests the helper function ```ip```:

            * check if raises AddrFormatError when invalid IP address
            * check if calls using incorrect version raises ValueError
            * check if IPv6 address returned as expected
        """

        self.assertTrue(HAS_NETADDR)

        # test that raises AddrFormatError when wrong format
        self.assertRaises(AddrFormatError, napalm_base.helpers.ip, 'fake')
        self.assertRaises(ValueError, napalm_base.helpers.ip, '2001:db8:85a3::8a2e:370:7334',
                          version=4)
        self.assertRaises(ValueError, napalm_base.helpers.ip, '192.168.17.1',
                          version=6)
        self.assertEqual(
          napalm_base.helpers.ip('2001:0dB8:85a3:0000:0000:8A2e:0370:7334'),
          '2001:db8:85a3::8a2e:370:7334'
        )
        self.assertEqual(
          napalm_base.helpers.ip('2001:0DB8::0003', version=6),
          '2001:db8::3'
        )

    def test_as_number(self):
        """Test the as_number helper function."""
        self.assertEqual(napalm_base.helpers.as_number('64001'), 64001)
        self.assertEqual(napalm_base.helpers.as_number('1.0'), 65536)
        self.assertEqual(napalm_base.helpers.as_number('1.100'), 65636)
        self.assertEqual(napalm_base.helpers.as_number('1.65535'), 131071)
        self.assertEqual(napalm_base.helpers.as_number('65535.65535'), 4294967295)
        self.assertEqual(napalm_base.helpers.as_number(64001), 64001)

    def test_convert_uptime_string_seconds(self):
        """
        Tests the parser function ```convert_uptime_string_seconds```:

            * check if all raw uptime strings passed return the expected uptime in seconds
        """

        # Regex 1
        self.assertEqual(convert_uptime_string_seconds('24 days,  11 hours,  25 minutes'), 2114700)
        self.assertEqual(convert_uptime_string_seconds('1 hour,  5 minutes'), 3900)
        self.assertEqual(convert_uptime_string_seconds('1 year,  2 weeks, 5 minutes'), 32745900)
        self.assertEqual(
            convert_uptime_string_seconds('95 weeks, 2 days, 10 hours, 58 minutes'), 57668280)
        self.assertEqual(
            convert_uptime_string_seconds('26 weeks, 2 days, 7 hours, 7 minutes'), 15923220)
        self.assertEqual(
            convert_uptime_string_seconds('19 weeks, 2 days, 2 hours, 2 minutes'), 11671320)
        self.assertEqual(
            convert_uptime_string_seconds('15 weeks, 3 days, 5 hours, 57 minutes'), 9352620)
        self.assertEqual(
            convert_uptime_string_seconds('1 year, 8 weeks, 15 minutes'), 36375300)
        self.assertEqual(
            convert_uptime_string_seconds('8 weeks, 2 hours, 5 minutes'), 4845900)
        self.assertEqual(
            convert_uptime_string_seconds('8 weeks, 2 hours, 1 minute'), 4845660)
        self.assertEqual(
            convert_uptime_string_seconds('2 years, 40 weeks, 1 day, 22 hours, 3 minutes'),
            87429780)
        self.assertEqual(
            convert_uptime_string_seconds('2 years, 40 weeks, 1 day, 19 hours, 46 minutes'),
            87421560)
        self.assertEqual(
            convert_uptime_string_seconds('1 year, 39 weeks, 15 hours, 23 minutes'), 55178580)
        self.assertEqual(
            convert_uptime_string_seconds('33 weeks, 19 hours, 12 minutes'), 20027520)
        self.assertEqual(
            convert_uptime_string_seconds('33 weeks, 19 hours, 8 minutes'), 20027280)
        self.assertEqual(
            convert_uptime_string_seconds('33 weeks, 19 hours, 10 minutes'), 20027400)
        self.assertEqual(
            convert_uptime_string_seconds('51 weeks, 5 days, 13 hours, 0 minutes'), 31323600)
        self.assertEqual(
            convert_uptime_string_seconds('51 weeks, 5 days, 12 hours, 57 minutes'), 31323420)
        self.assertEqual(
            convert_uptime_string_seconds('51 weeks, 5 days, 12 hours, 55 minutes'), 31323300)
        self.assertEqual(
            convert_uptime_string_seconds('51 weeks, 5 days, 12 hours, 58 minutes'), 31323480)

        # Regex 2
        self.assertEqual(convert_uptime_string_seconds('114 days, 22:27:32'), 9930452)
        self.assertEqual(convert_uptime_string_seconds('0 days, 22:27:32'), 80852)
        self.assertEqual(convert_uptime_string_seconds('365 days, 5:01:44'), 31554104)

        # Regex 3
        self.assertEqual(convert_uptime_string_seconds('7w6d5h4m3s'), 4770243)
        self.assertEqual(convert_uptime_string_seconds('95w2d10h58m'), 57668280)
        self.assertEqual(convert_uptime_string_seconds('1h5m'), 3900)


class FakeNetworkDriver(NetworkDriver):

    def __init__(self):
        """Connection details not needed."""
        pass

    def load_merge_candidate(self, config=None):
        """
        This method is called at the end of the helper ```load_template```.
        To check whether the test arrives at the very end of the helper function,
        will return True instead of raising NotImplementedError exception.
        """
        return True
