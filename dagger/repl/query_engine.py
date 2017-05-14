import dagger.graph
import dagger.graph_consts
import copy


def get_flattened_deps(g, library, edge_type):
    """Returns all the dependencies which are explicitly satisfied"""

    lib_node = g.get_node(library)
    if lib_node is None:
        return None
    deps = set()
    libraries = set([library])
    visited = set([library])

    while True:
        if len(libraries) == 0:
            break

        new_libs = set()

        for library in libraries:
            if edge_type == dagger.graph_consts.LIB_LIB:
                children = g.get_edge_type(dagger.graph_consts.LIB_LIB).get(library)
            else:
                implicit_dep_graph = get_implicit_lib_deps(g, library)
                if implicit_dep_graph is None:
                    continue
                children = implicit_dep_graph.get_edge_type(dagger.graph_consts.IMP_LIB_LIB).get(library)

            if children is None:
                continue

            deps.update([g.get_node(child) for child in children])
            new_libs = new_libs | (children - visited)

        libraries = new_libs

    return deps

def get_extra_links(g, library):
    pass

def get_link_paths(g, source, target):
    """Returns a list of tuples, each tuple representing a path from
    node 1 to node 2, implemented via recursive dfs"""
    source_node = g.get_node(source)
    target_node = g.get_node(target)

    if None in (source_node, target_node):
        return None

    if source_node.type == dagger.graph_consts.NODE_LIB:
        direct_deps = g.get_edge_type(dagger.graph_consts.LIB_LIB).get(source)
    elif source_node.type == dagger.graph_consts.NODE_EXE:
        direct_deps = g.get_edge_type(dagger.graph_consts.EXE_LIB).get(source)

    paths = []

    if len(direct_deps) == 0:
        return None

    for lib in direct_deps:
        compute_link_paths(g, source, target, lib, paths, [source],  set([source]))

    return paths

def compute_link_paths(g, source, target, lib, paths, path, visited):
    """Computes all the paths between two libraries, or an executable and a library"""

    direct_deps = g.get_edge_type(dagger.graph_consts.LIB_LIB).get(lib)
    if lib == target:
        path.append(target)
        paths.append(path)
        return
    if lib in visited:
        return
    if direct_deps is None:
        return

    visited.update([lib])
    path.append(lib)
    for child in direct_deps:
        compute_link_paths(g, source, target, child, paths, copy.deepcopy(path), visited)



def find_symbol_leaks(g, library):
    """Finds all the symbols that are required, but not defined within this library
    or any of its explicit direct explicit dependencies"""

    lib_node = g.get_node(library)
    explicit_dependencies = g.get_edge_type(dagger.graph_consts.LIB_LIB).get(library)

    symbols_defined = lib_node.defined_symbols

    if explicit_dependencies is not None:
        for lib in explicit_dependencies:
            symbols_defined.update(g.get_node(lib).defined_symbols)

    symbols_used = g.get_edge_type(dagger.graph_consts.LIB_SYM).get(library)
    symbols_used_clean = set()

    if symbols_used is None:
        return None

    for symbol in symbols_used:
        if g.get_node(symbol).files is not None and len(
                g.get_node(symbol).files) > 0:
            symbols_used_clean.add(symbol)

    return set([g.get_node(x)
                for x in symbols_used_clean.difference(symbols_defined)])

def get_lib(g, id):
    """returns the lib this file/symbol is contained in as a set of nodes.
    Multiply defined symbols can have more than one lib in which it's defined"""

    node = g.get_node(id)

    if node is None:
        return
    if node.type is dagger.graph_consts.NODE_FILE:
        return set([g.get_node(node.library)])
    elif node.type is dagger.graph_consts.NODE_SYM:
        return set([g.get_node(id) for id in node.libs])

def get_file(g, id):
    """returns the file this symbol is contained in. Multiply defined symbols can have more than one
    file in which it's defined"""

    node = g.get_node(id)

    if node is None:
        return
    if node.type is dagger.graph_consts.NODE_SYM:
        return set([g.get_node(id) for id in node.files])

def get_dependent_libs(g, id):
    """returns the libraries which are dependent on the given symbol, lib, or
    file id"""

    target_node = g.get_node(id)

    if target_node is None:
        return None
    if target_node.type == dagger.graph_consts.NODE_LIB:
        edge_type = dagger.graph_consts.LIB_LIB
    elif target_node.type == dagger.graph_consts.NODE_SYM:
        edge_type = dagger.graph_consts.LIB_SYM
    else:
        edge_type = dagger.graph_consts.LIB_FIL

    return gen_incoming_subgraph(g, id, "dependent_libs", edge_type)


def find_node(g, id):
    """returns a node given the node id"""

    return g.get_node(id)

def get_dependent_files(g, id):
    """returns the files which are dependent on the given symbol, lib, or file id"""

    target_node = g.get_node(id)

    if target_node is None:
        return None
    if target_node.type == dagger.graph_consts.NODE_LIB:
        edge_type = dagger.graph_consts.FIL_LIB
    elif target_node.type == dagger.graph_consts.NODE_SYM:
        edge_type = dagger.graph_consts.FIL_SYM
    else:
        edge_type = dagger.graph_consts.FIL_FIL

    return gen_incoming_subgraph(g, id, "dependent_files", edge_type)

def get_defined_symbols(g, id):
    """returns the symbols which are defined in the given file or library"""
    node = g.get_node(id)

    if node is None:
        return None
    if node.type not in (dagger.graph_consts.NODE_LIB, dagger.graph_consts.NODE_FILE):
        raise TypeError()
    if node.defined_symbols is None:
        return node
    return set([g.get_node(id) for id in node.defined_symbols])

def get_defined_files(g, id):
    """returns the files which are defined in the given library"""

    node = g.get_node(id)

    if node is None:
        return None
    if node.type != dagger.graph_consts.NODE_LIB:
        raise TypeError()
    if node.defined_files is None:
        return node
    return set([g.get_node(id) for id in node.defined_files])

def get_file_deps(g, id):
    """returns the files which the given lib or file depends on"""

    node = g.get_node(id)
    if node is None:
        return None
    if node.type == dagger.graph_consts.NODE_LIB:
        edge_type = dagger.graph_consts.LIB_FIL
    elif node.type == dagger.graph_consts.NODE_FILE:
        edge_type = dagger.graph_consts.FIL_FIL
    else:
        raise TypeError()

    return gen_outgoing_subgraph(g, id, edge_type)

def get_symbol_deps(g, id):
    """returns the symbols which the given lib or file depends on"""

    node = g.get_node(id)
    if node is None:
        return None
    if node.type == dagger.graph_consts.NODE_LIB:
        edge_type = dagger.graph_consts.LIB_SYM
    elif node.type == dagger.graph_consts.NODE_FILE:
        edge_type = dagger.graph_consts.FIL_SYM
    else:
        raise TypeError("node type '{0}', with id of '{0}'".format(node.type, id))

    return gen_outgoing_subgraph(g, id, edge_type)

def get_lib_deps_f(g, id):
    """returns the libraries that a file depends on"""

    node = g.get_node(id)
    if node is None:
        return None
    if node.type != dagger.graph_consts.NODE_FILE:
        raise TypeError()

    return gen_outgoing_subgraph(g, id, dagger.graph_consts.FIL_LIB)

def get_explicit_lib_deps(g, id):
    """returns the libraries that a library explicitly depends on"""
    node = g.get_node(id)
    if node is None:
        return None

    if node.type not in (dagger.graph_consts.NODE_LIB, dagger.graph_consts.NODE_EXE):
        raise TypeError()

    if node.type == dagger.graph_consts.NODE_LIB:
        return gen_outgoing_subgraph(g, id, dagger.graph_consts.LIB_LIB)
    else:
        return gen_outgoing_subgraph(g, id, dagger.graph_consts.EXE_LIB)

# TODO populate these in the SCons tool under the edgetype dagger.graph_consts.IMP_LIB_LIB
def get_implicit_lib_deps(g, id):
    """returns the libraries that a library implicitly depends on"""

    source_node = g.get_node(id)

    if source_node is None:
        return None

    if source_node.type == dagger.graph_consts.NODE_LIB:
        edge_type = dagger.graph_consts.IMP_LIB_LIB
        symbols = g.get_edge_type(dagger.graph_consts.LIB_SYM).get(id)
    elif source_node.type == dagger.graph_consts.NODE_EXE:
        edge_type = dagger.graph_consts.EXE_LIB
        symbols = g.get_edge_type(dagger.graph_consts.LIB_SYM).get(id)
    else:
        raise TypeError()

    deps = set()
    if symbols is None:
        return None

    for symbol in symbols:
        symbol_node = g.get_node(symbol)
        if symbol_node.libs is not None:
            for lib in symbol_node.libs:
                if lib != id and lib is not None:
                    deps. add(lib)

    if len(deps) == 0:
        return None

    nodes = {k: v for (k, v) in zip(deps, (g.get_node(id) for id in deps))}
    nodes[id] = source_node
    sub_graph = dagger.graph.Graph()
    sub_graph.nodes = nodes
    sub_graph.get_edge_type(dagger.graph_consts.IMP_LIB_LIB)[id] = deps
    return sub_graph

# TODO test and fix this function
def detect_cycles(g):
    """Returns a list of lists, where each list represents a cycle found in the graph"""

    lib_nodes = (x for x in g._nodes.keys() if g.get_node(
        x).type == dagger.graph_consts.NODE_LIB)

    cycles = set()

    for lib in lib_nodes:
        imp_deps = [x.id for x in get_flattened_imp_deps(g, lib)]
        if lib in imp_deps:
            print lib
            cycle = detect_lib_cycle(g, lib, set(), ())
            if cycle is not None:
                cycles.add(cycle)

    return [x for x in cycles if x[0] == x[-1]]


def detect_lib_cycle(g, lib, visited, path):
    if lib in visited:
        return path + (lib,)

    visited.update([lib])
    implicit_dep_graph = get_implicit_lib_deps(g, lib)

    if implicit_dep_graph is None:
        return None

    deps = implicit_dep_graph.get_edge_type(dagger.graph_consts.IMP_LIB_LIB)[lib]

    for dep in deps:
        cycle = detect_lib_cycle(g, dep, visited.copy(), path + (lib,))
        if cycle is not None:
            return cycle

def gen_outgoing_subgraph(g, source, edge_type):
    """Generates a subgraph for queries that ask about direct edge relationships such as FIL_LIB,
    LIB_LIB, LIB_SYM etc."""

    source_node = g.get_node(source)

    if source_node is None:
        return dagger.graph_consts.NODE_NOT_FOUND

    dep_set = g.get_edge_type(edge_type).get(source)

    if dep_set is None:
        return None

    # need intermediate variable because of the way graph.nodes' setter works
    nodes = zip_nodes(g, dep_set)
    nodes[source] = source_node

    sub_graph = dagger.graph.Graph()
    sub_graph.nodes = nodes
    sub_graph.get_edge_type(edge_type)[source] = set(dep_set)
    return sub_graph


def gen_incoming_subgraph(g, target, field, edge_type):
    """Generates a subgraph for queries that ask about incoming edge relationships, such as which
    libraries are dependent on the given target file or library"""

    target_node = g.get_node(target)
    if field == "dependent_libs":
        source_set = target_node.dependent_libs
    elif field == "dependent_files":
        source_set = target_node.dependent_files

    if source_set is None:
        # Maybe just return a single node object as a graph instead of None?
        return None

    nodes = zip_nodes(g, source_set)
    nodes[target] = target_node

    sub_graph = dagger.graph.Graph()
    sub_graph.nodes = nodes

    for id in source_set:
        sub_graph.get_edge_type(edge_type)[id] = set([target])

    return sub_graph

def zip_nodes(g, source_set):
    return  {
        k: v for (
            k,
            v) in zip(
            source_set,
            (g.get_node(id) for id in source_set))}
