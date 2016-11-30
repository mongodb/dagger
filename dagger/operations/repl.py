import os
import sys
import cmd
import argh
import logging

import dagger.repl.query_engine
import dagger.graph
import dagger.graph_consts


def print_incoming_graph(g, edge_type):
    if g is None:
        return

    for dep in sorted(g.get_edge_type(edge_type).keys()):
        print(dep)

def print_outgoing_graph(g, source, edge_type):
    if g is None:
        return

    for dep in sorted(g.get_edge_type(edge_type).get(source)):
        print(dep)

def print_node_set(nodes):
    if nodes is None:
        return

    for node in sorted(nodes):
        print(node.id)

def print_node(node):
    for attr, value in node.__dict__.iteritems():
        print(str(attr) + ":" + "\n" + str(value))

def print_paths(paths):
    for path in paths:
        print(" -> ".join(path))
        print("-------------------")

class QueryRepl(cmd.Cmd):
    prompt = '>> '

    def import_graph(self, path):
        """Imports the dagger.graph, and calls cmdloop to start the repl"""

        print("Importing graph into query engine from JSON")
        self.g = dagger.graph.Graph(path)
        print("Successfully imported graph, start querying! "
               "Type 'help' for a list of query commands")
        self.cmdloop()

    def do_get_flattened_exp_deps(self, line):
        """Gets the flattened list of explicit library dependencies"""
        if self.g.get_node(line) is None:
            print("Node ID not valid")
        print_node_set(dagger.repl.query_engine.get_flattened_deps(self.g, line,
            dagger.graph_consts.LIB_LIB))

    def do_get_flattened_imp_deps(self, line):
        """Gets the flattened list of implicit library dependencies"""
        if self.g.get_node(line) is None:
            print("Node ID not valid")
        print_node_set(dagger.repl.query_engine.get_flattened_deps(self.g, line,
            dagger.graph_consts.IMP_LIB_LIB))

    def do_get_link_paths(self, line):
        """Usage: get_link_paths libA libB , Gets the link paths from LibA to LibB
        or an executable to a library"""
        source, target = line.split(" ")
        print_paths(dagger.repl.query_engine.get_link_paths(self.g, source, target))

    def do_get_node(self, line):
        """Prints all information about a node object"""
        if self.g.get_node(line) is None:
            print("Node ID not valid")

        print_node(self.g.get_node(line))

    def do_symbol_leaks(self, line):
        """Returns the symbols that are needed by this library, but not defined
        within the library or any of it's explicit dependencies"""

        print_node_set(dagger.repl.query_engine.find_symbol_leaks(self.g, line))

    def do_get_dependent_libs(self, line):
        """Gets all the libraries dependent on this symbol, file, or library"""

        node = self.g.get_node(line)
        if node is None:
            print("Node ID does not exist")
            return

        if node.type == dagger.graph_consts.NODE_LIB:
            edge_type = dagger.graph_consts.LIB_LIB

        elif node.type == dagger.graph_consts.NODE_SYM:
            edge_type = dagger.graph_consts.LIB_SYM

        else:
            edge_type = dagger.graph_consts.LIB_FIL

        print_incoming_graph(
            dagger.repl.query_engine.get_dependent_libs(
                self.g, line), edge_type)

    def do_get_dependent_files(self, line):
        """Gets all files dependent on this symbol, file, or library"""

        node = self.g.get_node(line)

        if node is None:
            print("Node ID does not exist")
            return

        if node.type == dagger.graph_consts.NODE_LIB:
            edge_type = dagger.graph_consts.FIL_LIB

        elif node.type == dagger.graph_consts.NODE_SYM:
            edge_type = dagger.graph_consts.FIL_SYM

        else:
            edge_type = dagger.graph_consts.FIL_FIL

        print_incoming_graph(
            dagger.repl.query_engine.get_dependent_files(
                self.g, line), edge_type)

    def do_get_explicit_lib_deps(self, line):
        """Gets this libraries explicitly defined dependencies"""

        node = self.g.get_node(line)

        if node is None:
            print("Node ID does not exist")
            return

        if node.type not in (dagger.graph_consts.NODE_LIB, dagger.graph_consts.NODE_EXE):
            print("Node is not a valid type for this query")
            return

        if node.type == dagger.graph_consts.NODE_LIB:
            edge_type = dagger.graph_consts.LIB_LIB
        else:
            edge_type = dagger.graph_consts.EXE_LIB

        print_outgoing_graph(dagger.repl.query_engine.get_explicit_lib_deps(self.g, line),
                line, edge_type)

    def do_get_implicit_lib_deps(self, line):
        """Gets all implicit library dependencies for this library"""

        node = self.g.get_node(line)

        if node is None:
            print("Node ID does not exist")
            return

        if node.type != dagger.graph_consts.NODE_LIB:
            print("Node is not a valid type for this query")
            return

        print_outgoing_graph(dagger.repl.query_engine.get_implicit_lib_deps(self.g, line), line, dagger.graph_consts.IMP_LIB_LIB)

    def do_get_symbol_deps(self, line):
        """Gets all symbol dependencies for this library or file"""

        node = self.g.get_node(line)

        if node is None:
            print("Not a valid Node ID")
            return

        if node.type == dagger.graph_consts.NODE_LIB:
            edge_type = dagger.graph_consts.LIB_SYM
        elif node.type == dagger.graph_consts.NODE_FILE:
            edge_type = dagger.graph_consts.FIL_SYM
        else:
            print("Node is not a valid type for this query")
            return

        print_outgoing_graph(
            dagger.repl.query_engine.get_symbol_deps(
                self.g, line), line, edge_type)

    def do_get_defined_symbols(self, line):
        """Gets all symbols defined in this library or file"""

        node = self.g.get_node(line)

        if node is None:
            print("Not a valid Node ID")
            return

        if node.type not in (dagger.graph_consts.NODE_LIB, dagger.graph_consts.NODE_FILE):
            print("Node is not of valid type for this operation")
            return

        print_node_set(dagger.repl.query_engine.get_defined_symbols(self.g, line))

    def do_get_defined_files(self, line):
        """Gets all the files defined within this library"""

        node = self.g.get_node(line)

        if node is None:
            print("Not a valid Node ID")
            return

        if node.type not in (dagger.graph_consts.NODE_LIB, dagger.graph_consts.NODE_FILE):
            print("Node is not of valid type for this operation")
            return

        print_node_set(dagger.repl.query_engine.get_defined_files(self.g, line))

    def do_get_file(self, line):
        """Gets the file/files this symbol is defined in"""

        node = self.g.get_node(line)
        if node is None:
            print("Not a valid Node ID")
            return
        nodes = dagger.repl.query_engine.get_file(self.g, line)
        if nodes is None:
            return
        print_node_set(nodes)

    def do_get_lib(self, line):
        """Gets the lib/libs this symbol is defined in"""

        nodes = dagger.repl.query_engine.get_lib(self.g, line)

        if nodes is None:
            return

        print_node_set(nodes)

    def do_get_file_deps(self, line):
        """Gets the files this file/library depends on"""

        node = self.g.get_node(line)
        if node is None:
            print("Not a valid Node ID")
            return

        if node.type == dagger.graph_consts.NODE_LIB:
            edge_type = dagger.graph_consts.LIB_FIL
        elif node.type == dagger.graph_consts.NODE_FILE:
            edge_type = dagger.graph_consts.FIL_FIL
        else:
            print("Not a valid node for this query")
            return

        print_outgoing_graph(
            dagger.repl.query_engine.get_file_deps(
                self.g, line), line, edge_type)

    def do_get_lib_deps_f(self, line):
        """Gets the libraries this file depends on"""

        print_outgoing_graph(dagger.repl.query_engine.get_lib_deps_f(self.g, line), line, graph_consts.FIL_LIB)

    def do_detect_cycles(self, line):
        """Returns the cycles found in this dagger.graph"""

        print_paths(dagger.repl.query_engine.detect_cycles(self.g))

    def do_exit(self, line):
        "Exits the repl"

        print("Quitting the query engine - Goodbye!")
        raise SystemExit()


@argh.arg("path", help="path to file", default="foo.json")
@argh.expects_obj
@argh.named("repl")
def main(args):
    try:
        QueryRepl().import_graph(args.path)
    except ValueError:
        logging.error("Your json data is malformed, do a rebuild")
    except IOError:
        logging.error("cannot open", args.path)
