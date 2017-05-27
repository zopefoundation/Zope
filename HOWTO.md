# How to maintain the Zope versions page

The [Zope version configuration page](./README.md) and the linked
version and requirements files are built from a special branch of
the [Zope GitHub repository](https://github.com/zopefoundation/Zope).

```bash
  $ git clone -b gh-pages git@github.com:zopefoundation/Zope
  $ cd Zope
  $ ./build_indexes
  $ git add README.md releases/
  $ git commit -m "Add new Zope releases."
  $ git push origin gh-pages
```

The end result is available at https://zopefoundation.github.io/Zope/.

