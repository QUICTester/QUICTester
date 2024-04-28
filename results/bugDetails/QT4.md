# QT4

## Bug Description
Neqo server crashes when attempting to dereference a null pointer in cases where the selected input sequence contains an INITIAL_CONNECTION_CLOSE message that precedes an INITIAL_CLIENT_HELLO message. This bug is also guaranteed to occur when the input sequence includes the INITIAL_CONNECTION_CLOSE message but lacks the INITIAL_CLIENT_HELLO message. Based on our findings, it appears that the server attempts to respond with a CONNECTION_CLOSE message. However, it cannot obtain the connection's primary path when creating the message. This happens because the server will only set a primary path for that connection when it receives and process an INITIAL_CLIENT_HELLO message.

## Impacted Servers & Versions
Neqo (Tested on commit aaabc1c1)

## Fixed Version
This bug has been fixed in commit [ac51239](https://github.com/mozilla/neqo/pull/1814).

## Input Sequence
[Input.INITIAL_CONNECTION_CLOSE]
