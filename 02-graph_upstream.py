import os

import github3
import networkx as nx
import requests
from pkg_resources import parse_version


def source_location(meta_yaml):
    # TODO: use get
    # TODO: have dict
    try:
        if 'github.com' in meta_yaml['url']:
            return 'github'
        elif 'pypi.python.org' in meta_yaml['url']:
            return 'pypi'
        elif 'pypi.org' in meta_yaml['url']:
            return 'pypi'
        elif 'pypi.io' in meta_yaml['url']:
            return 'pypi'
        else:
            print(meta_yaml['url'])
            return None
    except KeyError:
        return None


def pypi_version(meta_yaml, gh):
    """Copyright (c) 2017, Peter M. Landwehr"""
    pypi_name = meta_yaml['url'].split('/')[6]
    r = requests.get('https://pypi.python.org/pypi/{}/json'.format(
        pypi_name))
    if not r.ok:
        with open('upstream_bad', 'a') as f:
            f.write('{}: Could not find version on pypi\n'.format(meta_yaml['name']))
        print('Could not find version on pypi', pypi_name)
        return False
    return r.json()['info']['version'].strip()


def gh_version(meta_yaml, gh):
    split_url = meta_yaml['url'].lower().split('/')
    package_owner = split_url[split_url.index('github.com') + 1]
    gh_package_name = split_url[split_url.index('github.com') + 2]

    # get all the tags
    repo = gh.repository(package_owner, gh_package_name)
    if not repo:
        with open('upstream_bad', 'a') as f:
            f.write('{}: could not find repo\n'.format(meta_yaml['name']))
        print("could not find repo", gh_package_name)
        return False

    rels = [parse_version(r.name) for r in
            repo.iter_tags() if 'rc' not in r.name]
    if len(rels) == 0:
        with open('upstream_bad', 'a') as f:
            f.write('{}: no tags found\n'.format(meta_yaml['name']))
        print("no tags found", gh_package_name)
        return False

    return max(rels)


sl_map = {'pypi': {'version': pypi_version},
          'github': {'version': gh_version}}


def get_latest_version(meta_yaml, gh):
    sl = source_location(meta_yaml)
    if sl is None:
        print('Not on GitHub or pypi', meta_yaml['name'])
        return False
    rv = sl_map[sl]['version'](meta_yaml, gh)
    return rv


# gx = nx.read_yaml('graph.yml')
gx = nx.read_gpickle('graph.pkl')

gh = github3.login(os.environ['USERNAME'], os.environ['PASSWORD'])

for node, attrs in gx.node.items():
    try:
        print(node)
        attrs['new_version'] = get_latest_version(attrs, gh)
        print(attrs['version'], attrs['new_version'])
    except github3.GitHubError as e:
        print(e)
        pass
# nx.write_yaml(gx, 'graph2.yml')
nx.write_gpickle(gx, 'graph2.pkl')
