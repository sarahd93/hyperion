# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021 Greenbone Networks GmbH
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from uuid import uuid4

from unittest.mock import patch

from selene.tests import SeleneTestCase, GmpMockFactory


@patch('selene.views.Gmp', new_callable=GmpMockFactory)
class ExportVulnerabilitiesByIdsTestCase(SeleneTestCase):
    def setUp(self):
        self.id1 = uuid4()
        self.id2 = uuid4()

    def test_require_authentication(self, _mock_gmp: GmpMockFactory):
        response = self.query(
            f'''
            mutation {{
                exportVulnerabilitiesByIds(ids: ["{self.id1}", "{self.id2}"]) {{
                   exportedEntities
                }}
            }}
            '''
        )

        self.assertResponseAuthenticationRequired(response)

    def test_export_vulnerabilities_by_ids(self, mock_gmp: GmpMockFactory):
        self.login('foo', 'bar')

        mock_xml = (
            '<get_vulns_response status="200" status_text="OK">'
            f'<vuln id="{self.id1}">'
            '<name>some_name1</name>'
            '</vuln>'
            f'<vuln id="{self.id2}">'
            '<name>some_name2</name>'
            '</vuln>'
            '</get_vulns_response>'
        )

        mock_gmp.mock_response('get_vulnerabilities', mock_xml)

        response = self.query(
            f'''
            mutation {{
                exportVulnerabilitiesByIds(ids: ["{self.id1}", "{self.id2}"]) {{
                   exportedEntities
                }}
            }}
            '''
        )

        json = response.json()

        self.assertResponseNoErrors(response)

        vulnerabilities_xml = json['data']['exportVulnerabilitiesByIds'][
            'exportedEntities'
        ]

        self.assertEqual(mock_xml, vulnerabilities_xml)
        mock_gmp.gmp_protocol.get_vulnerabilities.assert_called_with(
            filter=f'uuid= uuid={self.id1} uuid={self.id2} '
        )

    def test_export_empty_ids_array(self, mock_gmp: GmpMockFactory):
        self.login('foo', 'bar')

        mock_xml = (
            '<get_vulns_response status=\"200\" status_text=\"OK\">'
            '<filters id=\"\"><term>uuid= first=1 rows=10 sort=name</term>'
            '<keywords><keyword><column>uuid</column><relation>=</relation>'
            '<value /></keyword><keyword><column>first</column><relation>'
            '=</relation><value>1</value></keyword><keyword><column>rows'
            '</column><relation>=</relation><value>10</value></keyword>'
            '<keyword><column>sort</column><relation>=</relation><value>name'
            '</value></keyword></keywords></filters><sort><field>name<order>'
            'ascending</order></field></sort><vulns max=\"10\" '
            'start=\"1\" /><vuln_count>16<filtered>0</filtered>'
            '<page>0</page></vuln_count></get_vulns_response>'
        )
        mock_gmp.mock_response('get_vulnerabilities', bytes(mock_xml, 'utf-8'))

        response = self.query(
            '''
            mutation {
                exportVulnerabilitiesByIds(ids: []) {
                   exportedEntities
                }
            }
            '''
        )

        json = response.json()

        self.assertResponseNoErrors(response)

        vulnerabilities_xml = json['data']['exportVulnerabilitiesByIds'][
            'exportedEntities'
        ]

        self.assertEqual(mock_xml, vulnerabilities_xml)

        mock_gmp.gmp_protocol.get_vulnerabilities.assert_called_with(
            filter='uuid= '
        )
