###################################################################################
#
#    
#
#     Web Client 
#    .
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

{
    "name": "Web Client",
    "summary": """Odoo Web Client Extension""",
    "version": "12.0.3.0.0",
    "category": "Extra Tools",
    "license": "LGPL-3",
    "author": "Jupical Technologies Pvt. Ltd.",
    "depends": [
        "bus",
        "jt_web_utils",
    ],
    "data": [
        "template/assets.xml",
        "views/res_config_settings_view.xml",
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "application": False,
    "installable": True,
    
}