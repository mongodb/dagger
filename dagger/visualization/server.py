"""Dagger visualization tool

Run this server to start a web-based visualization of the build dependency graph
"""
import json
import collections
import datetime
import logging

import flask

import dagger.graph
import dagger.repl.query_engine as query_engine

app = flask.Flask("Dagger")

logger = logging.getLogger("dagger.visualization.server")


def map_node_type_to_str(num):
    if num == 1:
        return "Library"
    elif num == 2:
        return "Symbol"
    elif num == 3:
        return "File"
    elif num == 4:
        return "Artifact"

    raise ValueError("Node type should be 1,2, or 3 (is {0})".format(num))


def map_edge_type_to_str(num):
    if num == 1:
        return "LibraryToLibrary"
    if num == 2:
        return "LibraryToFile"
    if num == 3:
        return "FileToLibrary"
    if num == 4:
        return "FileToFile"
    if num == 5:
        return "FileToSymbol"
    if num == 6:
        return "LibraryToSymbol"
    if num == 7:
        return "ImplicitLibraryToLibrary"


def determine_group(node, groups):
    # we want to group on the relevant dir names
    # so scratch out the users/bigboy/code/mongo/build
    # and the filename

    def find_nth(haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start
    start = 0
    end = node.rfind("/")

    if "third_party" in node:
        return 0

    if node[start:end] in groups:
        return groups[node[start:end]]

    groups[node[start:end]] = len(groups) + 1
    return groups[node[start:end]]


def graph_obj_to_d3(g_obj):
    # desired format:
    # { "nodes": [{"type":"File", "id":0, "name":"opt/mongo/shm"}],
    #   "links": [{"source": 0, "target": 1, "type":"file_to_file", "linkId": "0,1"}]}

    # make copies of objs so we can add a d3-specific attr
    g_node_copies = {}

    # maintain local list of nodes newly discovered (compared to collections.OrderedDict nodes)
    # in this subgraph
    new_nodes = []

    # nothing in the graph
    if g_obj is None:
        return json.dumps({"nodes": [], "links": []})

    for g_node in g_obj.nodes.values():
        # if we already have this node in our graph, don't add it again
        # just make necessary data changes for d3
        if g_node.name in flask.session['nodes']:
            print "already here", g_node.name
            setattr(g_node, 'd3_index', flask.session['nodes'].keys().index(g_node.name))
            g_node_copies[g_node.name] = g_node
            continue

        node = {}
        node['type'] = map_node_type_to_str(g_node.type)

        # okay so this is a hack to work with d3
        # d3 expects source and target in its link object
        # these values must be indices for our nodes list
        # since we don't have that inherent property in here,
        # we create it, and copy the value to a new obj that we then poll to create links
        node['id'] = len(flask.session['nodes'])
        setattr(g_node, 'd3_index', len(flask.session['nodes']))
        g_node_copies[g_node.name] = g_node
        node['name'] = g_node.name
        node['group'] = determine_group(g_node.name, flask.session['groups'])
        if node['name'] not in flask.session['nodes']:
            flask.session['nodes'][node['name']] = node
            new_nodes.append(node)

    new_links = []
    for edge_type in g_obj.edges:
        if len(g_obj.edges[edge_type]) == 0:
            continue
        for from_node in g_obj.edges[edge_type]:
            for to_node in g_obj.edges[edge_type][from_node]:
                link = {}

                # g_node_copies[from_node].d3_index
                link['source'] = flask.session['nodes'][from_node]['id']

                # g_node_copies[to_node].d3_index
                link['target'] = flask.session['nodes'][to_node]['id']

                link['type'] = map_edge_type_to_str(edge_type)
                link['linkId'] = ','.join([
                    str(flask.session['nodes'][from_node]['id']),
                    str(flask.session['nodes'][to_node]['id'])
                ])
                link['weight'] = 1

                # add link to list of new links if it's new
                if link['linkId'] not in flask.session['links']:
                    new_links.append(link)
                flask.session['links'][link['linkId']] = link

    data = {"nodes": new_nodes, "links": new_links}
    return json.dumps(data)


def single_node_to_d3(node):
    d3_node = {}
    data = {'nodes': [d3_node], 'links': []}

    if node is None:
        logger.info("single node was empty")
        return json.dumps(data)

    d3_node['name'] = node.name
    d3_node['type'] = map_node_type_to_str(node.type)
    d3_node['id'] = len(nodes)
    d3_node['group'] = determine_group(node.name, flask.session['groups'])
    if d3_node['name'] not in flask.session['nodes']:
        flask.session['nodes'][d3_node['name']] = d3_node

    return json.dumps(data)


def set_of_nodes_to_d3(node_set):
    new_nodes = []
    data = {"nodes": new_nodes, "links":[]}

    if node_set is None:
        logger.info("set of nodes was empty")
        return json.dumps(data)

    for node in node_set:
        d3_node = {}
        d3_node['name'] = node.name
        d3_node['type'] = map_node_type_to_str(node.type)
        d3_node['id'] = len(nodes)
        d3_node['group'] = determine_group(node.name, flask.session['groups'])
        if d3_node['name'] not in flask.session['nodes']:
            flask.session['nodes'][d3_node['name']] = d3_node
        new_nodes.append(d3_node)

    return json.dumps(data)


def set_of_nodes_to_d3_for_sidebar(node_set):
    if node_set is None:
        return json.dumps({"nodes": [], "links": []})

    new_nodes = []
    for node in node_set:
        d3_node = {}
        d3_node['name'] = node.name
        d3_node['type'] = map_node_type_to_str(node.type)
        d3_node['id'] = len(flask.session['nodes'])
        d3_node['group'] = determine_group(node.name, flask.session['groups'])
        new_nodes.append(d3_node)

    data = {"nodes": new_nodes, "links": []}
    return json.dumps(data)


# ---- pages ----
@app.route('/')
def force_plot():
    flask.session.permanent = True
    flask.session['groups'] = {}
    flask.session['nodes'] = collections.OrderedDict()
    flask.session['links'] = collections.OrderedDict()

    return flask.render_template("force.html")


@app.route('/interactive')
def interactive_plot():
    flask.session.permanent = True
    flask.session['groups'] = {}
    flask.session['nodes'] = collections.OrderedDict()
    flask.session['links'] = collections.OrderedDict()

    return flask.render_template("interactive.html")


@app.route('/hive')
def hive_plot():
    flask.session.permanent = True
    flask.session['groups'] = {}
    flask.session['nodes'] = collections.OrderedDict()
    flask.session['links'] = collections.OrderedDict()

    return flask.render_template("hive.html")


# ---- static data ----
@app.route('/forcedata')
def force_data():
    return graph_obj_to_d3(None)


@app.route('/hivedata')
def hive_data():
    return graph_obj_to_d3(dep_graph)


# ---- interactive queries ----
@app.route('/query/<path:myquery>')
def query(myquery):
    """Queries should all be of format function_name node"""
    logger.debug("got query: {0}, which splits to: {1}".format(myquery, myquery.split()))
    func, node = myquery.split()
    logger.info("doing '{0}' query for '{1}'".format(func, node))

    # reset nodes and links for queries
    flask.session['nodes'] = collections.OrderedDict()
    flask.session['links'] = collections.OrderedDict()

    if func == "get_fil_to_lib_deps":
        sub_graph = query_engine.get_lib_deps_f(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_explicit_lib_deps":
        sub_graph = query_engine.get_explicit_lib_deps(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_implicit_lib_deps":
        sub_graph = query_engine.get_implicit_lib_deps(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_fil_deps":
        sub_graph = query_engine.get_file_deps(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_sym_deps":
        sub_graph = query_engine.get_symbol_deps(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_dep_libs":
        sub_graph = query_engine.get_dependent_libs(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_dep_files":
        sub_graph = query_engine.get_dependent_files(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_dep_syms":
        sub_graph = query_engine.get_dependent_symbols(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    elif func == "get_lib":
        sub_graph = query_engine.get_lib(dep_graph, node)
        return single_node_to_d3(sub_graph)
    elif func == "get_file":
        sub_graph = query_engine.get_file(dep_graph, node)
        return single_node_to_d3(sub_graph)
    elif func == "get_inc_edges":
        sub_graph = query_engine.get_inc_edges(dep_graph, node)
        return graph_obj_to_d3(sub_graph)
    else:
        raise ValueError("{0} is not a valid query, should be 'function node'".format(func))


@app.route('/impldeps/<path:node>')
def get_impl_deps(node):
    return graph_obj_to_d3(query_engine.get_implicit_lib_deps(dep_graph, node))


@app.route('/expldeps/<path:node>')
def get_deps(node):
    return graph_obj_to_d3(query_engine.get_explicit_lib_deps(dep_graph, node))


@app.route('/filetolibdeps/<path:node>')
def get_fil_to_lib_deps(node):
    return graph_obj_to_d3(query_engine.get_lib_deps_f(dep_graph, node))


@app.route('/fildeps/<path:node>')
def get_fil_deps(node):
    return graph_obj_to_d3(query_engine.get_file_deps(dep_graph, node))


# TODO this still doesn't work pretty sure
@app.route('/inc/<path:node>')
def get_inc_edges(node):
    # TODO specify where these edges are coming frpom for d3 purposes
    return graph_obj_to_d3(query_engine.gen_incoming_subgraph(dep_graph, node, "dependent_libs", 2))


@app.route('/defdsyms/<path:node>')
def get_defined_symbols(node):
    return set_of_nodes_to_d3_for_sidebar(query_engine.get_defined_symbols(dep_graph, node))


@app.route('/defdfiles/<path:node>')
def get_defined_files(node):
    return set_of_nodes_to_d3_for_sidebar(query_engine.get_defined_files(dep_graph, node))


@app.route('/fileinfo/<path:node>')
def get_file_info(node):
    return set_of_nodes_to_d3_for_sidebar(query_engine.get_file(dep_graph, node))


@app.route('/libinfo/<path:node>')
def get_lib_info(node):
    return set_of_nodes_to_d3_for_sidebar(query_engine.get_lib(dep_graph, node))


@app.route('/symleaks/<path:node>')
def find_symbol_leaks(node):
    return set_of_nodes_to_d3_for_sidebar(query_engine.find_symbol_leaks(dep_graph, node))


def start_app(graph_file="library_dependency_graph.json"):
    app.permanent_session_lifetime = datetime.timedelta(minutes=100)
    global dep_graph
    dep_graph = dagger.graph.Graph(graph_file)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.use_reloader = False
    app.debug = False
    app.run()
