#!/bin/bash
# build_dist.sh - Builds the iDigi Connector for Arduino Distribution Archive
# Copyright (c) 2012 Jordan Husney
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#############
# Settinigs #
#############

# Max number of arguments, empty vaule = unlimited arguments
SCRIPT_MAX_ARGS=0

#########################
# Common Initialization #
#########################

SCRIPT_NAME="$(basename "$0")"
# Stores arguments
SCRIPT_ARGS=()
# Stores option flags
SCRIPT_OPTS=()
# For returning value after calling SCRIPT_OPT
SCRIPT_OPT_VALUE=

#############
# Functions #
#############

usage () {
  echo "Usage: $SCRIPT_NAME [options] [arguments]

Options:
  -o, --output_file   output ZIP archive filename
  -h, --help           display this help and exit
"  
}

parse_options() {
  while (( $#>0 )); do
    opt="$1"
    arg="$2"
    
    case "$opt" in
      -o|--output_file)
        SCRIPT_OPT_SET "output_file" "$arg" 1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      -*)
        echo "$SCRIPT_NAME: invalid option -- '$opt'" >&2
        echo "Try \`$SCRIPT_NAME --help' for more information." >&2
        exit 1
        ;;
      *)
        if [[ ! -z $SCRIPT_MAX_ARGS ]] && (( ${#SCRIPT_ARGS[@]} == $SCRIPT_MAX_ARGS )); then
          echo "$SCRIPT_NAME: cannot accept any more arguments -- '$opt'" >&2
          echo "Try \`$SCRIPT_NAME --help' for more information." >&2
          exit 1
        else
          SCRIPT_ARGS=("${SCRIPT_ARGS[@]}" "$opt")
        fi
        ;;
    esac
    shift
  done
}

###########################
# Script Template Functions

# Stores options
# $1 - option name
# $2 - option value
# $3 - non-empty if value is not optional
SCRIPT_OPT_SET () {
  if [[ ! -z "$3" ]] && [[ -z "$2" ]]; then
    echo "$SCRIPT_NAME: missing option value -- '$opt'" >&2
    echo "Try \`$SCRIPT_NAME --help' for more information." >&2
    exit 1
  fi
  # XXX should check duplication, but doesn't really matter
  SCRIPT_OPTS=("${SCRIPT_OPTS[@]}" "$1" "$2")
}

# Checks if an option is set, also set SCRIPT_OPT_VALUE.
# Returns 0 if found, 1 otherwise.
SCRIPT_OPT () {
  local i opt needle="$1"
  for (( i=0; i<${#SCRIPT_OPTS[@]}; i+=2 )); do
    opt="${SCRIPT_OPTS[i]}"
    if [[ "$opt" == "$needle" ]]; then
      SCRIPT_OPT_VALUE="${SCRIPT_OPTS[i+1]}"
      return 0
    fi
  done
  SCRIPT_OPT_VALUE=
  return 1
}

########
# Main #
########

parse_options "$@"

# start to do something

XIG_VERSION=`grep -m1 "VERSION" ../../src/xig.py | sed -e 's/VERSION =//' -e 's/"//g' -e 's/[ \t]*//g'`
OUTPUT_FILE="xig-linux_src-${XIG_VERSION}.zip"

if SCRIPT_OPT "output_file"; then
  OUTPUT_FILE=${SCRIPT_OPT_VALUE}
fi

touch $OUTPUT_FILE
OUTPUT_FILE=`ls -1 $(pwd)/${OUTPUT_FILE}`
rm -f $OUTPUT_FILE

GIT_ARCHIVE_ALL=`ls -1 $(pwd)/git-archive-all.py`
OLD_PWD=$(pwd)

cd ../.. ; $GIT_ARCHIVE_ALL --prefix $(basename "$OUTPUT_FILE" .zip) $OUTPUT_FILE
cd $OLD_PWD

