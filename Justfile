alias c := check
alias t := test
alias ta := test-all

check:
    veryl check --quiet

test TEST *extra_args:
    uv run veryl test --wave --quiet {{justfile_directory()}}/src/tests/test_{{TEST}}.veryl \
        {{justfile_directory()}}/src/*.veryl \
        {{justfile_directory()}}/src/bram/*.veryl \
        {{justfile_directory()}}/src/wb/*.veryl \
        {{extra_args}}

test-all *EXTRA_ARGS:
    uv run veryl test --wave --quiet {{EXTRA_ARGS}}

fmt:
    uv run veryl fmt --quiet

wave file:
    surfer {{justfile_directory()}}/target/waveform/{{file}}.fst >& /dev/null & 