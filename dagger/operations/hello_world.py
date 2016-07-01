import argh


@argh.named("hello")
def main():
    """A simple 'hello world' example."""

    return "hello world!"
