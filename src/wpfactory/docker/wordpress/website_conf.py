#!/usr/bin/env python

import sys
import os

domain = sys.argv[1]

apache = """
<VirtualHost *:80>
    ServerName {name}

    DocumentRoot /var/www/test/root

    <Directory   /var/www/test/root>
        # Exec .php scripts via FastCGI:
        Options +ExecCGI

        # Acceptable overrides:
        # - FileInfo (.htacces-based rewrite rules)
        # - AuthConfig (.htaccess-based basic auth)
        AllowOverride All
    </Directory>

    ErrorLog  /var/log/apache2/{name}/error.log
    CustomLog /var/log/apache2/{name}/access.log combined
</VirtualHost>
"""

f = '/var/log/apache2/{name}'.format(name=domain)
if not os.path.exists(f):
    os.makedirs(f)

with open('/etc/apache2/sites-available/website.conf', 'w') as f:
    f.write(apache.format(name=domain))
