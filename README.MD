# `dagger` - tools for library dependency graph introspection
Dagger contains tools which help developers understand MongoDB's build dependency graph. Currently, this repository contains:

    1. query repl for asking various build dependency questions
    2. A visualizer for exploring the graph.

## Usage
Do a MongoDB build locally, or via Evergreen on OSX or Linux hosts, and generate the library_dependency_graph.json file (by default the tool will generate this file in the root of your mongo directory or by download via Evergreen)

```
scons dagger
```

In the root of the Dagger tool directory, install the virtualenv

```
make install
```

Activate the virtualenv

```
eval $(make activate)
```

Now the dagger repl is initialized, and we can kick off the visualizer or query repl.

To kick off the query repl: 

```
dagger repl /path/to/json/file 
```

# Queries

Now your query engine repl is kicked off. 

To see all available queries:
```
help
```

To see documentation for a query:
```
help query_name
```


# Examples
Find the explicit direct library dependencies
```
get_explicit_lib_deps build/opt/mongo/transport/libtransport_layer_common.a 
```

Find implicit library dependencies 
```
get_implicit_lib_deps build/opt/mongo/transport/libtransport_layer_common.a 
```

Find the paths from LibA to LibB, or from EXE to LIB

```
get_link_paths build/opt/mongo/mongod build/opt/mongo/unittest/libunittest.a
```
Find the symbol leaks in a library (the symbols that a library implicitly needs but are not satisfied by its explicit direct dependencies)
```
symbol_leaks build/opt/mongo/unittest/libunittest.a
```
