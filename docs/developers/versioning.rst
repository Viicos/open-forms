.. _developers_versioning:

Versioning policy
=================

Because Open Forms ("as a suite") is a collection of components developed individually
from each other, it's important to be aware of the compatible versions to guarantee
that the application(s) keep working as expected.

We identify three major components having their own version numbers:

* Open Forms API, the API implemented by the Open Forms backend
* Open Forms SDK, the client application consuming the API
* Open Forms backend, implements the API, administrative interface and various
  modules/plugins (see :ref:`developers_architecture`).

The Open Forms SDK and Open Forms API versions must be aligned with each other for
correct functioning of the forms.

All versions adhere to `semantic versioning <https://semver.org/>`_, meaning major
versions may introduce breaking changes and minor versions are backwards compatible.

Open Forms SDK
--------------

The SDK follows its own semantic versioning scheme. Major versions typically mean that
users of the Javascript interfaces are impacted (npm package users or users modifying
the window global directly in their own code).

Whenever new features are added to the SDK that depend on certain API functionality
being available, then *at least* the minor version of the SDK will be bumped.

Newer minor API versions should be compatible with a given minor SDK version, per the
semantic versioning principles.

The table below documents the required API version ranges for a given SDK version. The
maximum API version should usually not be applicable, unless the SDK relies on
experimental feature changes (see :ref:`developers_versioning_api`).

.. table:: Required API version ranges
   :widths: auto

   =========== =================== ===================
   SDK version minimum API version maximum API version
   =========== =================== ===================
   1.0.x       1.0.y               < 2.0.0
   1.0.4       1.0                 < 2.0.0
   1.1.0       1.1.0               < 2.0.0
   1.1.1       1.1.1               < 2.0.0
   1.2.x       2.0.y               < 2.1.0
   1.3.0       2.1.0               n/a
   1.4.0       2.2.0               n/a
   1.5.0       2.3.0               n/a
   =========== =================== ===================

.. _developers_versioning_api:

Open Forms API
--------------

The Open Forms API adheres to semantic versioning with one exception: experimental
functionality.

We use the `specification extension`_ pattern in the API spec to mark functionality
as experimental, using the ``x-experimental: true`` flag. Experimental functionality
may introduce breaking changes in minor versions, but not in patch versions.

We use this to mark parts of the API that we are not yet convinced about that they
are the right implementation. Release notes of Open Forms backend will include which
experimental functionality was changed.

.. _specification extension: https://swagger.io/specification/#specification-extensions

Open Forms backend
------------------

The Open Forms backend implements the Open Forms API, form submission processing and
various features related to forms happening at runtime.

Changes in the backend may result in changes to the API schema, but this is not a
guarantee. Many things happen "under the hood" that change or improve the API behaviour
in a backwards-compatible way without affecting the API schema.

This means that:

* the Open Forms backend version may be greater than the Open Forms API version (=
  changes did not affect the API schema)
* the backend version is always *at least* the API version - changes affecting the
  schema result in an API version bump.
* Breaking changes result in an major version increase for both backend and API

The matrix below documents which API version ranges are implemented by which Open Forms
backend version.

.. table:: API version offered by backend version
   :widths: auto

   =============== ===========
   Backend version API version
   =============== ===========
   2.3.x           2.3.y
   2.2.x           2.2.y
   2.1.x           2.1.y
   2.0.x           2.0.y
   1.1.x           1.1.y
   1.1.3           1.1.1
   1.0.x           1.0.y
   1.0.8           1.0.1
   1.0.11          1.0.2
   =============== ===========
