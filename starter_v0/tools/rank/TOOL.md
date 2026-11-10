---
name: rank
track: core
kind: local_formatter
provider: local Python
requires_env: []
inputs: [items, by, limit]
outputs: [items, by, item_count]
side_effect: false
---
# rank

Sort existing research items. `by=date` puts newer dates first and items without a
parseable date last. `by=title` sorts titles A–Z. `limit` keeps the first N items
after sorting; `0` keeps all. Does not search, fetch, or score claims. Malformed
`items` or an unknown `by` return an error dictionary. Input objects are not modified.
