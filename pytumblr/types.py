"""Runtime-safe aliases corresponding to the richer static definitions in types.pyi.

These remain plain dictionaries at runtime so PyTumblr keeps its historical
return-value semantics.
"""

Blog = dict
Post = dict
TrailItem = dict
ContentBlock = dict
LayoutBlock = dict
MediaObject = dict
