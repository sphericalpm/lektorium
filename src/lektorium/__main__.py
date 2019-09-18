import sys
import aiohttp.web
from . import app


repo_type_names = [x.name for x in app.RepoType]
auth = '' if len(sys.argv) < 3 else sys.argv[2]
if len(sys.argv) < 2 or sys.argv[1].upper() not in repo_type_names:
    message = 'Please provide repo type as argument. Use one of: {}'
    print(message.format(', '.join(repo_type_names)), file=sys.stderr)
    sys.exit(1)
repo_type = app.RepoType[sys.argv[1].upper()]
aiohttp.web.run_app(app.create_app(repo_type, auth), port=8000)
