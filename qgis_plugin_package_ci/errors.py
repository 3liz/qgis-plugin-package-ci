class PluginPackageError(Exception):
    pass


class VersionNotFoundError(PluginPackageError):
    pass
