#!/usr/bin/env sh
if [ -z "${husky_skip_init-}" ]; then
  debug () {
    if [ "${HUSKY_DEBUG-}" = "1" ]; then
      echo "husky (debug) - $1"
    fi
  }

  readonly hook_name="$(basename -- "$0")"
  debug "starting $hook_name..."

  if [ "$HUSKY" = "0" ]; then
    debug "HUSKY env variable is set to 0, skipping hook"
    exit 0
  fi

  if [ -f ~/.huskyrc ]; then
    echo "husky - '~/.huskyrc' is DEPRECATED, please move your code to ~/.config/husky/init.sh"
  fi
  i="${XDG_CONFIG_HOME:-$HOME/.config}/husky/init.sh"
  [ -f "$i" ] && . "$i"

  readonly husky_skip_init=1
  export husky_skip_init
  sh -e "$0" "$@"
  exitCode="$?"

  if [ "$exitCode" != "0" ]; then
    echo "husky - $hook_name script failed (code $exitCode)"
  fi

  if [ "$exitCode" = "127" ]; then
    echo "husky - command not found in PATH=$PATH"
  fi

  exit "$exitCode"
fi
