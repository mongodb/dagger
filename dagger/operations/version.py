import os
import json

import dagger

import argh
import libgiza
import yaml


def print_version(key, versions, prefix=""):
    print("{0}{1}: {2}".format(prefix, key, versions[key]))


@argh.named("version")
@argh.arg("--json", dest="_print_json_output", default=False, action="store_true",
          help="output a json document")
@argh.expects_obj
def main(args):
    versions = {
        "dagger": dagger.__version__,
        "dependencies": {
            "libgiza": libgiza.__version__,
            "yaml": yaml.__version__,
            "argh": argh.__version__,
        },
    }

    if args._print_json_output:
        print(json.dumps(versions, indent=3, sort_keys=True))
    else:
        print_version("dagger", versions)
        print("dependencies:")
        for dep in versions["dependencies"].keys():
            print_version(dep, versions["dependencies"], prefix="   ")
