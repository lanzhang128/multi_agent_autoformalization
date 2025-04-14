#!/bin/bash

args=$*

cd $REPL_PATH
echo $args | $ELAN_HOME/bin/lake exe repl
