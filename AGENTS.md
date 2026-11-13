# Working rules

Read STYLE.md first, Principles included, and follow it for every file you touch.

- Never guess catalog facts. Bitmap names, sizes, formats, palette sizes and offsets come from `rvt/data/osos-2.0.5.json` or from the reversing repository; extension asset names and sizes from `rvt/data/extensions.json`. If the catalog does not have it, say so.
- Never commit Apple pixels or firmware bytes: no stock bitmaps, no decrypted images, no files derived from them except names, sizes, offsets and checksums. Themes carry their own art or rules the iPod applies to the stock art; a recolour rule may name the stock colours it replaces.
- `rvt/data/rvt.h` is the format contract the Appearance extension vendors byte for byte; a change to it is a change on both sides.
- Python follows Ruff with a line length of 88; run `ruff check .`, `ruff format --check .` and `python3 -m unittest discover -s tests` before saying a change works.
- Keep the change to what was asked. Put unrelated findings in the conversation.
- Commit and push only when asked. No generated-by trailers in commit messages.
