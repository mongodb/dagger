import logging
import traceback

import argh
import libgiza.error

import dagger.config.cli
import dagger.operations.hello_world
import dagger.operations.version

logger = logging.getLogger("dagger.cli")

commands = {
    "main": [
        dagger.operations.hello_world.main,
        dagger.operations.version.main,
        ],
}

# creates the parser object and defines global options *above* any
def get_base_parser():
    """
    Adds global arguments/settings and creates the top-level argument parser
    object.
    """

    parser = argh.ArghParser()
    parser.add_argument('--level', '-l',
                        help="set the logging level for the application.",
                        choices=['debug', 'warning', 'info', 'critical', 'error'],
                        default='info')

    return parser


def main():
    """
    The main entry point, as specified in the ``setup.py`` file. Adds commands
    from other subsidiary entry points (specified in the ``commands`` variable
    above,) and then uses ``arch.dispatch()`` to start the process.

    The "DaggerConfig" object allows the application to delegate all
    argument parsing validation using setters and getters in the object where
    arg(h)parse stores the configuration data.

    This function catches and recovers from :exc:`KeyboardInterupt` which means
    that doesn't dump a stack trace following a Control-C.
    """

    parser = get_base_parser()

    for namespace, entry_points in commands.items():
        if namespace == 'main':
            argh.add_commands(parser, entry_points)
        else:
            argh.add_commands(parser, entry_points, namespace=namespace)

    args = dagger.config.cli.DaggerCliConfig()

    # set the logging level early to ensure logging is configured during
    # argument parsing.
    args.level = "info"

    # run the command, catching user-interruption and common error types directly.
    try:
        argh.dispatch(parser, namespace=args)
    except KeyboardInterrupt:
        logger.error('operation interrupted by user.')
        exit(1)
    except RuntimeError:
        logger.error("exiting due to a runtime error")
        exit(1)
    except (ValueError, TypeError, AttributeError) as e:
        # catch data access and validation errors, and, in common operation,
        # suppress the traceback, unless logging at debug level.

        logger.info("error: {0}, type: {1}".format(e, type(e)))
        tb = traceback.format_exc()
        err = libgiza.error.Error(message=("encountered data validation or access "
                                           "error during normal operation."),
                                  fatal=True, include_trace=True)
        err.payload = {"type": type(e), "error": e, "trace": tb}
        logger.debug(err.render_output())
        logger.debug("exception traceback: \n" + tb)
        exit(1)


if __name__ == '__main__':
    main()
