.. _Web-API:

======================================
VOLTTRON User Interface API
======================================

The VOLTTRON User Interface API (VUI) is provided by the VOLTTRON Web Service, and is
intended to provide capabilities for building fully featured frontend applications.
The VUI is a RESTful HTTP API for communicating with components of the VOLTTRON system.

Installation
------------
The VUI is a built-in part of the VOLTTRON Web Service. To enable to VOLTTRON Web Service,
bootstrap VOLTTRON within the virtual environment using the `--web` option:

.. code-block:: bash

    python boostrap.py --web

Path Structure
---------------


Paths to endpoints consist of alternating constant and variable segments, and are designed
to be readable and discoverable:

.. image:: files/path_structure.png


Available Endpoints
-------------------


Endpoints which are currently provided by the API are described in detail in the
following sections:

- `Authentication <authentication-endpoints.html>`_
- `Platforms <platform-endpoints.html>`_
    - `Agents <agent-endpoints.html>`_
        - `RPC <rpc-endpoints.html>`_
    - `Devices <device-endpoints.html>`_
    - `Historians <historian-endpoints.html>`_
    - `Pubsub <pubsub-endpoints.html>`_
