import threading
import logging

import argh

import dagger.visualization.server

logger = logging.getLogger("dagger.operations.viz")


@argh.named("viz")
@argh.arg("path", help="path to file", default="libdeps.json")
@argh.expects_obj
def main(args):
    logger.info("starting server now... (initialization takes several seconds)")
    logger.info("open: http://127.0.0.1:5000/interactive")
    dagger.visualization.server.start_app(args.path)

    # t = threading.Thread(
    #     target=,
    #     args=[args.path])
    # t.daemon = True
    # t.start()

    # # webbrowser.open(url)
    # raw_input("Enter anything to kill server\n")
