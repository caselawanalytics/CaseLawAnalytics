#!/bin/bash

#Populates the triple store with the given turtle file.
namespace=caselaw
format="application/x-turtle"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
java -cp ~/blazegraph/blazegraph.jar com.bigdata.rdf.store.DataLoader -verbose -format $format -namespace $namespace $DIR/RWStore.properties #1

