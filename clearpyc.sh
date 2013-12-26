#!/bin/bash

find . -name "*.pyc" -exec rm {}  \;
find . -name "*~" -exec rm {}  \;