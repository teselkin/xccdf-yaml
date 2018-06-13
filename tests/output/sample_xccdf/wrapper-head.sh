#!/bin/bash
set -o errtrace
set -o nounset
set -o pipefail
declare -A XCCDF_RESULT
XCCDF_RESULT[CONTINUE]=100
XCCDF_RESULT[PASS]=${XCCDF_RESULT_PASS:-101}
XCCDF_RESULT[FAIL]=${XCCDF_RESULT_FAIL:-102}
XCCDF_RESULT[ERROR]=${XCCDF_RESULT_ERROR:-103}
XCCDF_RESULT[UNKNOWN]=${XCCDF_RESULT_UNKNOWN:-104}
XCCDF_RESULT[NOT_APPLICABLE]=${XCCDF_RESULT_NOT_APPLICABLE:-105}
XCCDF_RESULT[NOT_CHECKED]=${XCCDF_RESULT_NOT_CHECKED:-106}
XCCDF_RESULT[NOT_SELECTED]=${XCCDF_RESULT_NOT_SELECTED:-107}
XCCDF_RESULT[INFORMATIONAL]=${XCCDF_RESULT_INFORMATIONAL:-108}
XCCDF_RESULT[FIXED]=${XCCDF_RESULT_FIXED:-109}
exit_with(){
  set +o xtrace
  local status=${1:-ERROR}
  local ec=${XCCDF_RESULT[${status}]:-${XCCDF_RESULT[ERROR]}}
  echo "Exiting with status ${status}(${ec})"
  exit ${ec}
}
trap_error(){
  local ec=${1:-0}
  if [[ ${ec} == 100 ]]; then
    return
  elif [[ ${ec} -gt 100 && ${ec} -lt 110 ]]; then
    exit ${ec}
  else
    exit ${XCCDF_RESULT[ERROR]}
  fi
}
trap 'trap_error $?' ERR
set -o xtrace
