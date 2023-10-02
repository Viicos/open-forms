.. _configuration_prefill_haal_centraal:

==========================
Haal Centraal BRP bevragen
==========================

`Haal Centraal`_ is an initiative to transform the currently used SOAP-services
to consult the base registration, to modern RESTful API's.

The `Haal Centraal BRP bevragen API`_ allows you to retrieve personal
information about the person filling out the form, based on the BSN.

.. note::

   This service contains sensitive data and requires a connection to a specific
   client system. Currently however, there are very few suppliers who offer
   this service.

   On the `Haal Centraal BRP bevragen API`_ Github, you can request credentials
   for a test environment that uses an API key.

.. _`Haal Centraal BRP bevragen API`: https://github.com/VNG-Realisatie/Haal-Centraal-BRP-bevragen
.. _`Haal Centraal`: https://vng-realisatie.github.io/Haal-Centraal/


Configuration
=============

1. Obtain credentials to access the Haal Centraal BRP bevragen API
2. In Open Forms, navigate to: **Configuration** > **Services**
3. Click **Add service** and fill in the following details:

   * **Label**: *Fill in a human readable label*, for example: ``My BRP API``
   * **Type**: ORC (Overige)
   * **API root URL**: *URL provided by supplier*
   * **Authorization type**: API key *(but can differ per supplier)*
   * **Header key**: Authorization
   * **Header value**: *The API key from step 1*

4. Click **Save**
5. Navigate to **Configuration** > **Configuration overview**. In the **Prefill plugins**
   group, click on **Configuration** for the **Haal Centraal: BRP Personen Bevragen**
   line.
6. Select for the **BRP Personen Bevragen API**, the **[ORC (Overige)] My BRP API**
   option, that we just created in step 3.
7. Select the correct version for **BRP Personen Bevragen API version** - new
   installations likely use ``v2.0``.
8. Click **Save**

The Haal Centraal configuration is now complete.


Technical
=========

================  ===================
API               Supported versions
================  ===================
BRP bevragen API  2.0
BRP bevragen API  1.3
================  ===================
