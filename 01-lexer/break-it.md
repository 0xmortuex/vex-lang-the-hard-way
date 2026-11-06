# Break It: The Lexer

## Challenge 1: Put `=` before `==`

In `PUNCTUATION`, move `"="` to the very front of the list and run `python 01-lexer/verify.py`.
Which assertion fails first, and what do the tokens of `a == b` look like now?

**Hint:** The loop takes the first punctuation string that matches at position `i`. With `"="` first
it always wins, so `==` becomes two tokens. Every "maximal munch" lexer needs its alternatives
ordered longest first (or a rule that picks the longest match).

## Challenge 2: Forget to record positions

Change `Token(word ..., start)` for identifiers to use `0` as the position. Everything still lexes.
Run `python 08-errors/verify.py` first. What breaks, and how far from the lexer is the symptom? Then
run `python 01-lexer/verify.py`.

**Hint:** Chapters 2 to 7 keep working, which is the trap. Positions are only *used* by error
reporting, so the bug shows up as carets under the wrong column in chapter 8. Bugs whose symptom is
several modules away from their cause are the expensive ones, so chapter 1's `verify.py` checks the
positions of identifiers directly, at the source, and fails too.

## Challenge 3: A number glued to a word

Remove the `if i < n and (text[i].isalpha() ...)` check after reading digits. What does `lex("12abc")`
return? Write the parse error you would get for `let x = 12abc;` and decide whether the original check is
worth its three lines.

**Hint:** You get `INT(12)` then `IDENT(abc)`, and the parser reports "expected `;`, found `abc`", which says
nothing about the real problem. The lexer is the only stage that knows the two tokens were adjacent.
