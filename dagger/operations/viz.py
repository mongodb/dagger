import logging
from argh import named, arg, expects_obj
import webbrowser

import dagger.visualization.server as viz_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dagger.operations.viz")

@named("viz")
@arg("path", help="Path to the file", default="libdeps.json")
@expects_obj
def main(args):
    
    server_url = "http://127.0.0.1:5000/interactive"
    
    logger.info("Starting server now... (initialization takes several seconds)")
    logger.info(f"Open: {server_url}")
    
    viz_server.start_app(args.path)
    
    webbrowser.open(server_url)
    
    input("Press Enter to exit...\n")
