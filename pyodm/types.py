class NodeOption:
    """A node option available to be passed to a node.

    Args:
        domain (str): Valid range of values
        help (str): Description of what this option does
        name (str): Option name
        value (str): Default value for this option
        type (str): One of: ['int', 'float', 'string', 'bool', 'enum']
    """
    def __init__(self, domain, help, name, value, type):
        self.domain = domain
        self.help = help
        self.name = name
        self.value = value
        self.type = type