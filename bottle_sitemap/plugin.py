# coding=utf-8
"""BottleSitemap main class implementation.

Copyright (C) 2018  Manolis Tsoukalas.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.
If not, see <https://www.gnu.org/licenses/>.
"""
import re

from bottle import jinja2_template, response

from bottle_sitemap.error import ResourceDoesntExist, SitemapBackendNotFound


def create_static_link(domain: str, site_name: str, link: object) -> str:
    """Function for creating static links.
    :param domain: the domain scope http or https. Default is http.
    :param site_name: your site name. (test-site.com)
    :param link: the endpoint. (/hello)
    :return: returns a full link for the sitemap. (http://test-site.com/hello)
    """
    return '{}://{}{}'.format(domain, site_name, link.rule)


def create_dynamic_link(domain: str, site_name: str, link: object, resource_keys: list) -> list:
    """Function for creating dynamic links.
    This function gets the link_resources key from route config.
    The link_resources is a list with an object with keys the resource names.
    example:
        [{'user_id': '1','item': 'foo'}]
    :param domain: the domain scope http or https. Default is http.
    :param site_name: your site name. (test-site.com)
    :param link: the endpoint. (/hello/<user_id:int>/<item>)
    :param resource_keys: the keys contained in the url. ([<user_id:int>, <item>])
    :return: returns a full list with links for the sitemap. ([http://test-site.com/hello/1/foo])
    """
    resources = link.config().get('link_resources')

    if resources:
        dynamic_links = []
        for resource in resources:
            sitemap_dynamic_link = link.rule

            for key in resource_keys:
                link_without_filter = re.search(r'<(\w+)>', sitemap_dynamic_link)
                link_with_filter = re.search(r'<(\w+):(\w+)>', sitemap_dynamic_link)

                if link_without_filter:
                    resource_key_name = link_without_filter.group(1)
                    sitemap_dynamic_link = str.replace(sitemap_dynamic_link, key, resource[resource_key_name])

                if link_with_filter:
                    resource_key_name = link_with_filter.group(1)
                    try:
                        sitemap_dynamic_link = str.replace(sitemap_dynamic_link, key, resource[resource_key_name])
                    except KeyError:
                        raise ResourceDoesntExist(
                            'Resource {} not found in the backend.'.format(resource_key_name))
            dynamic_links.append('{}://{}{}'.format(domain, site_name, sitemap_dynamic_link))

        return dynamic_links
    else:
        raise SitemapBackendNotFound("Sitemap link_resources not found. Can't create dynamic link without a backend.")


class BottleSitemap(object):
    """ This plugin creates a endpoint and generates a sitemap
    based on routes marked with the add_to_sitemap=True config.
    For adding dynamic links in your sitemap you must provide
    a list with an object with keys the resource names.

    For example:
        @app.route('/test/<user_id:int>/<item>', add_to_sitemap=True, link_resources=[{'user_id': '1','item': 'foo'}])
    """

    api = 2

    def __init__(self, site_name: str, sitemap_endpoint: str, keyword: str = 'bottle_sitemap', domain: str = 'http',
                 changefreq: str = 'monthly', priority: float = 0.5):
        self.keyword = keyword
        self.domain = domain
        self.site_name = site_name
        self.sitemap_endpoint = sitemap_endpoint
        self.changefreq = changefreq
        self.priority = priority

    def setup(self, app):
        """ Make sure that other installed plugins don't affect the same
            keyword argument."""
        for other in app.plugins:
            if not isinstance(other, BottleSitemap):
                continue

            if other.keyword == self.keyword:
                raise PluginError("Found another BottleSitemap plugin with conflicting settings (non-unique keyword).")

        @app.get(self.sitemap_endpoint)
        def generate_sitemap():
            """The view for generating the sitemap in xml format.
            :return: sitemap in xml format.
            """
            response.add_header('Content-Type', 'application/xml')

            links_for_sitemap = [link for link in app.routes if link.config.get('add_to_sitemap')]

            sitemap_links = []
            for link in links_for_sitemap:
                resource_keys = [item for item in re.findall(r'(<\w+:?\w+>)', link.rule)]

                if resource_keys:
                    result = create_dynamic_link(self.domain, self.site_name, link, resource_keys)
                    sitemap_links.extend(result)
                else:
                    result = create_static_link(self.domain, self.site_name, link)
                    sitemap_links.append(result)

            return jinja2_template('''<?xml version="1.0" encoding="UTF-8"?>
                    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                        {% for url in sitemap_links %}
                        <url>
                            <loc>{{url}}</loc>
                            <changefreq>{{changefreq}}</changefreq>
                            <priority>{{priority}}</priority>
                        </url>
                        {% endfor %}
                    </urlset>
            ''', {'sitemap_links': sitemap_links, 'changefreq': self.changefreq, 'priority': self.priority})

    def apply(self, callback, context):
        # Override global configuration with route-specific values.

        def wrapper(*args, **kwargs):
            return callback(*args, **kwargs)

        # Replace the route callback with the wrapped one.
        return wrapper
