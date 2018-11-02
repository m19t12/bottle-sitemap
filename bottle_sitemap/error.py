# coding=utf-8
class SitemapError(Exception):
    pass


class SitemapBackendNotFound(SitemapError):
    pass


class BackendError(SitemapError):
    pass


class ResourceDoesntExist(BackendError):
    pass
